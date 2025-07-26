from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated

from fastapi import UploadFile
from pydantic import BaseModel, Field, model_validator, field_validator
from fastapi import HTTPException, status
from app.schemas.validators import protection_against_xss
import uuid

class BookStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class OrderByEnum(str, Enum):  
    DATE_OF_PUBLISH = "date_of_publish"
    PRICE = "price"

class CoverImageSchema(BaseModel):
    image_url: str
    images: list[UploadFile]


Price = Annotated[Decimal, Field(ge=0, max_digits=6, decimal_places=2)]


class BookCreateSchema(BaseModel, extra="forbid"):
    title: str = Field(..., max_length=100)
    description: str
    price: Price
    date_of_publish: date = Field(...)
    contributing_authors: Annotated[
        list[str],
        Field(
            description="Must be authors. Not regular users.",
        ),
    ] = []
    status: BookStatusEnum
    number_of_items: int = Field(ge=0, title="the number of books avaliable to buy")
    images: list[UploadFile] = []

    @field_validator("images")
    @classmethod
    def validate_image(cls, value: list[UploadFile]):
        allowed_ext = ["jpeg", "jpg", "png"]
        for image in value:
            filename = image.filename.lower()
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

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values):
        protection_against_xss(values.get("title"))
        protection_against_xss(values.get("description"))
        return values


class BookResponseCreateSchema(BaseModel):
    success: str


class CoverImageModel(BaseModel):
    cover_id:uuid.UUID
    image_url:str
    book_id:uuid.UUID

class BookFilterResponse(BaseModel):
    book_id:uuid.UUID
    date_of_publish:date
    price:Decimal
    number_of_items: int
    description:str
    title:str
    contributing_authors:list[str]
    status:BookStatusEnum
    author_id:uuid.UUID
    cover_images:list[CoverImageModel]
 