# auth_schemas.py — backward-compatibility shim
# Schemas have been split into request_schemas.py and response_schemas.py.
# This re-exports everything so existing imports keep working.
from .request_schemas  import SignupRequest, LoginRequest, RefreshTokenRequest
from .response_schemas import TokenPair, AccessTokenResponse, LogoutResponse, UserPublic, SignupResponse, LoginResponse

__all__ = [
    "SignupRequest", "LoginRequest", "RefreshTokenRequest",
    "TokenPair", "AccessTokenResponse", "LogoutResponse",
    "UserPublic", "SignupResponse", "LoginResponse",
]
