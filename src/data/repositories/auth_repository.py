import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.exceptions import DatabaseError
from src.data.models.postgres import User, UserRole, Role, RefreshToken

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RoleRepository
# ---------------------------------------------------------------------------

class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, role_name: str) -> Role | None:
        try:
            result = await self.db.execute(select(Role).where(Role.role_name == role_name))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_role_by_name failed | role=%s error=%s", role_name, exc)
            raise DatabaseError("Failed to fetch role") from exc


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_email failed | email=%s error=%s", email, exc)
            raise DatabaseError("Failed to fetch user by email") from exc

    async def get_by_id(self, user_id: int) -> User | None:
        try:
            result = await self.db.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_id failed | user_id=%s error=%s", user_id, exc)
            raise DatabaseError("Failed to fetch user by id") from exc

    async def create(self, name: str, email: str, password_hash: str) -> User:
        """Creates a user with the default 'finance_associate' role."""
        return await self.create_with_role(name, email, password_hash, "finance_associate")

    async def create_with_role(self, name: str, email: str, password_hash: str, role_name: str) -> User:
        """Creates a user and assigns the given role via the user_roles table."""
        try:
            # 1. Fetch the role row
            role_repo = RoleRepository(self.db)
            role = await role_repo.get_by_name(role_name)
            if not role:
                raise DatabaseError(f"Role '{role_name}' not found in roles table")

            # 2. Create the user
            user = User(name=name, email=email, password_hash=password_hash)
            self.db.add(user)
            await self.db.flush()  # get user_id

            # 3. Assign the role
            user_role = UserRole(user_id=user.user_id, role_id=role.role_id)
            self.db.add(user_role)
            await self.db.flush()

            logger.debug("User staged with role | email=%s role=%s", email, role_name)
            return user
        except DatabaseError:
            raise
        except SQLAlchemyError as exc:
            logger.error("create_with_role failed | email=%s error=%s", email, exc)
            raise DatabaseError("Failed to create user") from exc

    async def get_all_by_role(self, role_name: str) -> list[User]:
        """Returns all users assigned to the given role."""
        try:
            result = await self.db.execute(
                select(User)
                .join(User.user_role)
                .join(UserRole.role)
                .where(Role.role_name == role_name)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            logger.error("get_all_by_role failed | role=%s error=%s", role_name, exc)
            raise DatabaseError("Failed to fetch users by role") from exc


# ---------------------------------------------------------------------------
# RefreshTokenRepository
# ---------------------------------------------------------------------------

class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> RefreshToken | None:
        try:
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.refresh_token == token)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_token failed | error=%s", exc)
            raise DatabaseError("Failed to fetch refresh token") from exc

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        try:
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.jti == jti)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            logger.error("get_by_jti failed | jti=%s error=%s", jti, exc)
            raise DatabaseError("Failed to fetch refresh token by jti") from exc

    async def create(
        self,
        user_id: int,
        jti: str,
        refresh_token: str,
        settings: Settings,
    ) -> RefreshToken:
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
            record = RefreshToken(
                user_id=user_id,
                jti=jti,
                refresh_token=refresh_token,
                is_revoked=False,
                expires_at=expires_at,
            )
            self.db.add(record)
            await self.db.flush()
            logger.debug("Refresh token staged | user_id=%s jti=%s", user_id, jti)
            return record
        except SQLAlchemyError as exc:
            logger.error("create refresh token failed | user_id=%s error=%s", user_id, exc)
            raise DatabaseError("Failed to create refresh token") from exc

    async def revoke(self, token_record: RefreshToken) -> None:
        try:
            token_record.is_revoked = True
            await self.db.flush()
            logger.debug("Refresh token revoked | token_id=%s jti=%s", token_record.token_id, token_record.jti)
        except SQLAlchemyError as exc:
            logger.error("revoke token failed | token_id=%s error=%s", token_record.token_id, exc)
            raise DatabaseError("Failed to revoke refresh token") from exc

    async def revoke_all_for_user(self, user_id: int) -> None:
        try:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
                .values(is_revoked=True)
            )
            await self.db.flush()
            logger.warning("All refresh tokens revoked | user_id=%s", user_id)
        except SQLAlchemyError as exc:
            logger.error("revoke_all_for_user failed | user_id=%s error=%s", user_id, exc)
            raise DatabaseError("Failed to revoke all tokens for user") from exc
