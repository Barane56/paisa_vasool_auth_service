from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token: Annotated[str, Field(description="Short-lived JWT access token")]
    refresh_token: Annotated[str, Field(description="Long-lived JWT refresh token")]
    token_type: Annotated[str, Field(description="Token type")] = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str = ""
    refresh_token: str = ""


class LogoutResponse(BaseModel):
    message: Annotated[str, Field(description="Success message")] = (
        "Successfully logged out"
    )


class UserPublic(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}


class SignupResponse(BaseModel):
    user: UserPublic
    tokens: TokenPair


class LoginResponse(BaseModel):
    user: UserPublic
    tokens: TokenPair
