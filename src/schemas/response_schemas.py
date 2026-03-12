# response_schemas.py — outbound auth response schemas
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token:  str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type:    str = Field(default="bearer")


class AccessTokenResponse(BaseModel):
    access_token:  str = ""
    refresh_token: str = ""


class LogoutResponse(BaseModel):
    message: str = Field(default="Successfully logged out")


class UserPublic(BaseModel):
    user_id:    int
    name:       str
    email:      EmailStr
    role:       str
    created_at: datetime
    model_config = {"from_attributes": True}


class SignupResponse(BaseModel):
    user:   UserPublic
    tokens: TokenPair


class LoginResponse(BaseModel):
    user:   UserPublic
    tokens: TokenPair
