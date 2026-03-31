import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.core.services import get_current_user, login, logout, signup
from src.core.services import refresh_token as refresh_token_service
from src.data.clients import get_db
from src.data.repositories import UserRepository
from src.schemas import (
    AccessTokenResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SignupRequest,
    SignupResponse,
    UserPublic,
)
from src.utils.jwt_utils import (
    TokenIdentity,
    _clear_access_cookie,
    _clear_refresh_cookie,
    _set_access_cookie,
    _set_refresh_cookie,
    get_current_user_id,
    hash_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


# ── POST /auth/signup ──────────────────────────────────────────────────────────


@router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup_route(
    body: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SignupResponse:
    result = await signup(body, db, settings)
    _set_access_cookie(response, result.tokens.access_token, settings)
    _set_refresh_cookie(response, result.tokens.refresh_token, settings)
    result.tokens.access_token = ""
    result.tokens.refresh_token = ""
    return result


# ── POST /auth/login ───────────────────────────────────────────────────────────


@router.post("/login", response_model=LoginResponse)
async def login_route(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    result = await login(body, db, settings)
    _set_access_cookie(response, result.tokens.access_token, settings)
    _set_refresh_cookie(response, result.tokens.refresh_token, settings)
    result.tokens.access_token = ""
    result.tokens.refresh_token = ""
    return result


# ── POST /auth/refresh ─────────────────────────────────────────────────────────


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_route(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AccessTokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
        )

    result = await refresh_token_service(refresh_token, db, settings)
    _set_access_cookie(response, result.access_token, settings)
    _set_refresh_cookie(response, result.refresh_token, settings)
    result.access_token = ""
    result.refresh_token = ""
    return result


# ── POST /auth/logout ──────────────────────────────────────────────────────────


@router.post("/logout", response_model=LogoutResponse)
async def logout_route(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
    identity: TokenIdentity = Depends(get_current_user_id),
) -> LogoutResponse:
    result = await logout(refresh_token, db)
    _clear_access_cookie(response)
    _clear_refresh_cookie(response)
    return result


# ── GET /auth/me ───────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserPublic)
async def me_route(
    db: AsyncSession = Depends(get_db),
    identity: TokenIdentity = Depends(get_current_user_id),
) -> UserPublic:
    return await get_current_user(identity.user_id, db)


# ─── Admin schemas ─────────────────────────────────────────────────────────────


class CreateFARequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    email: EmailStr
    password: Annotated[SecretStr, Field(min_length=8, max_length=128)]
    confirm_password: SecretStr

    @model_validator(mode="after")
    def passwords_match(self) -> "CreateFARequest":
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("password and confirm_password do not match")
        return self


class FAListResponse(BaseModel):
    items: list[UserPublic]
    total: int


# ── POST /auth/create-fa ───────────────────────────────────────────────────────


@router.post(
    "/create-fa", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def create_fa_route(
    body: CreateFARequest,
    db: AsyncSession = Depends(get_db),
    identity: TokenIdentity = Depends(get_current_user_id),
) -> UserPublic:
    if identity.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    user_repo = UserRepository(db)
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = await user_repo.create_with_role(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password.get_secret_value()),
        role_name="finance_associate",
    )
    await db.commit()
    await db.refresh(user)
    return UserPublic.model_validate(user)


# ── GET /auth/finance-associates ───────────────────────────────────────────────


@router.get("/finance-associates", response_model=FAListResponse)
async def list_fa_route(
    db: AsyncSession = Depends(get_db),
    identity: TokenIdentity = Depends(get_current_user_id),
) -> FAListResponse:
    if identity.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    user_repo = UserRepository(db)
    users = await user_repo.get_all_by_role("finance_associate")
    return FAListResponse(
        items=[UserPublic.model_validate(u) for u in users],
        total=len(users),
    )


# ── POST /auth/bootstrap-admin ─────────────────────────────────────────────────
#
# ONE-TIME endpoint — creates the first admin account.
# Self-locks: returns 409 if ANY admin already exists in the database.
# No authentication required (that's the whole point).
#
# curl example:
#     -d '{"name":"Administrator", \
#          "email":"admin@admin.com", \
#          "password":"changeme123", \
#          "confirm_password":"changeme123"}'


class BootstrapAdminRequest(BaseModel):
    name: Annotated[
        str, Field(min_length=2, max_length=100, examples=["Administrator"])
    ]
    email: Annotated[EmailStr, Field(examples=["admin@admin.com"])]
    password: Annotated[
        SecretStr, Field(min_length=8, max_length=128, examples=["changeme123"])
    ]
    confirm_password: Annotated[SecretStr, Field(examples=["changeme123"])]

    @model_validator(mode="after")
    def passwords_match(self) -> "BootstrapAdminRequest":
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("password and confirm_password do not match")
        return self


class BootstrapAdminResponse(BaseModel):
    message: str
    user: UserPublic


@router.post(
    "/bootstrap-admin",
    response_model=BootstrapAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bootstrap first admin (one-time, no auth required)",
    description=(
        "Creates the first admin account. "
        "**Returns 409 if an admin already exists** — "
        "making this endpoint safe to leave enabled; "
        "it is self-locking once used."
    ),
)
async def bootstrap_admin_route(
    body: BootstrapAdminRequest,
    db: AsyncSession = Depends(get_db),
) -> BootstrapAdminResponse:
    user_repo = UserRepository(db)

    # Refuse if any admin already exists — endpoint is one-time only
    existing_admins = await user_repo.get_all_by_role("admin")
    if existing_admins:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin account already exists. Use the normal login flow.",
        )

    # Also refuse if the email is already taken by a non-admin
    if await user_repo.get_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = await user_repo.create_with_role(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password.get_secret_value()),
        role_name="admin",
    )
    await db.commit()
    await db.refresh(user)

    logger.info(
        "Bootstrap admin created | email=%s user_id=%s", user.email, user.user_id
    )

    return BootstrapAdminResponse(
        message=f"Admin account created for {user.email}. This endpoint is now locked.",
        user=UserPublic.model_validate(user),
    )
