# auth_schemas.py — backward-compatibility shim
# Schemas have been split into request_schemas.py and response_schemas.py.
# This re-exports everything so existing imports keep working.
from .request_schemas import LoginRequest, RefreshTokenRequest, SignupRequest
from .response_schemas import (
    AccessTokenResponse,
    LoginResponse,
    LogoutResponse,
    SignupResponse,
    TokenPair,
    UserPublic,
)

__all__ = [
    "SignupRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenPair",
    "AccessTokenResponse",
    "LogoutResponse",
    "UserPublic",
    "SignupResponse",
    "LoginResponse",
]
