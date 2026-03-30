from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator


class SignupRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100, examples=["Jane Doe"])]
    email: Annotated[EmailStr, Field(examples=["jane@example.com"])]
    password: Annotated[
        SecretStr, Field(min_length=8, max_length=128, examples=["s3cr3tP@ss"])
    ]
    confirm_password: Annotated[SecretStr, Field(examples=["s3cr3tP@ss"])]

    @model_validator(mode="after")
    def passwords_match(self) -> "SignupRequest":
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("password and confirm_password do not match")
        return self


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, Field(examples=["jane@example.com"])]
    password: Annotated[SecretStr, Field(min_length=8, examples=["s3cr3tP@ss"])]


class RefreshTokenRequest(BaseModel):
    refresh_token: Annotated[
        str, Field(description="The refresh token issued at login or last refresh")
    ]
