import re
from enum import Enum
from typing import Annotated

from fastapi import HTTPException, UploadFile, status
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,

    
)
from decimal import Decimal


def password_constrains(value):
    """
    The validate_password function is used to check some
    constrains in the password submited by the user like
    password's length, to include one letter and to contain
    at least one number
    """
    if len(value) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if not re.search(r"[A-Za-z]", value):
        raise ValueError("Password must include at least one letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number.")
    return value


class ScopesEnum(str, Enum):
    USER = "user"
    AUTHOR = "author"





class UserAuthorSignUpSchema(BaseModel):
    name: str = Field(
        ..., max_length=100, description="username must not exceed 100 characters."
    )
    password: str
    email: EmailStr
    scopes: list[ScopesEnum]

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return password_constrains(value)

    model_config = ConfigDict(extra="forbid")


class SignUpSchemaResponse(BaseModel):
    success: str


class UpdateBookStatusSchema(BaseModel):
    pass


class DeactivateAccountResponseSchema(SignUpSchemaResponse):
    pass


class ReactivateAccountResponseSchema(SignUpSchemaResponse):
    pass


class Token(BaseModel):
    token_type: str
    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class LogoutResponseSchema(BaseModel):
    success: str


class NewAccessTokenResponseSchema(BaseModel):
    access_token: str


class UpdatePassword(BaseModel):
    """
    Schema for validating and updating a user's or author's password.
    Ensures password constraints and matching confirmation.
    """

    new_password: str
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value):
        return password_constrains(value)

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values):
        if values.get("new_password") != values.get("confirm_new_password"):
            raise ValueError("Passwords do not match!")
        return values


class UpdatePasswordResponseSchema(BaseModel):
    success: str


class UpdateEmailResponseSchema(BaseModel):
    success: str


class UpdateNameResponseSchema(BaseModel):
    success: str


class UpdateNameResponseSchema(BaseModel):
    success: str


class LogoutResponseSchema(UpdatePasswordResponseSchema):
    pass


class UpdateEmail(BaseModel):
    new_email: EmailStr


class UpdateName(BaseModel):
    new_name: str = Field(..., max_length=100, title="new name of the user")
    model_config = ConfigDict(extra="forbid")


class UploadImageSchema(BaseModel):
    image: UploadFile
    model_config = ConfigDict(extra="forbid")

    @field_validator("image")
    @classmethod
    def validate_image(cls, value):
        allowed_ext = ["jpeg", "jpg", "png"]  
        filename = value.filename.lower()
        parts = filename.split(".")
        if len(parts) > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name: Double extensions are not allowed. No more than one dot allowed.",
            )
        ext = parts[-1]
        if ext not in allowed_ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only jpeg, jpg, and png files are allowed for images.",
            )
        return value


class UploadImageResponseSchema(BaseModel):
    success: str


class RemovedUserAuthorAccountSchema(BaseModel):
    success: str

class BalanceUpdateSchemaResponse(BaseModel):
    success:str

class BalanceSchemaIn(BaseModel):
    value: Annotated[Decimal, Field(ge=0, max_digits=6, decimal_places=2)]

    model_config = ConfigDict(extra='forbid')