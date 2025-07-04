import re
from enum import Enum
from typing import List
from fastapi import UploadFile
from pydantic import (
    EmailStr,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


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


class BookStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class UserAuthorSignUpSchema(BaseModel):
    name: str = Field(
        ..., max_length=100, description="username must not exceed 100 characters."
    )
    password: str
    email: EmailStr
    scopes: List[ScopesEnum]

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
    new_name: str = Field(..., max_length=100)
    model_config = ConfigDict(extra="forbid")

class UploadImageSchema(BaseModel):
    image:UploadFile
    model_config = ConfigDict(extra="forbid")

class UploadImageResponseSchema(BaseModel):
    success:str