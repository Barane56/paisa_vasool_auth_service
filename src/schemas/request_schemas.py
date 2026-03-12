# request_schemas.py — inbound auth request schemas
from pydantic import BaseModel, EmailStr, Field, model_validator


class SignupRequest(BaseModel):
    name:             str      = Field(..., min_length=2, max_length=100, examples=["Jane Doe"])
    email:            EmailStr = Field(..., examples=["jane@example.com"])
    password:         str      = Field(..., min_length=8, max_length=128, examples=["s3cr3tP@ss"])
    confirm_password: str      = Field(..., examples=["s3cr3tP@ss"])

    @model_validator(mode="after")
    def passwords_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match")
        return self


class LoginRequest(BaseModel):
    email:    EmailStr = Field(..., examples=["jane@example.com"])
    password: str      = Field(..., min_length=8, examples=["s3cr3tP@ss"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token issued at login or last refresh")
