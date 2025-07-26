from pydantic import BaseModel, ConfigDict,field_validator
from app.schemas.validators import protection_against_xss

class AuthorDescription(BaseModel):
    description: str 
    model_config = ConfigDict(extra="forbid")

    @field_validator("description")
    @classmethod
    def validate(cls, value):
        protection_against_xss(value)
        return value




class AuthorDescriptionResponse(BaseModel):
    success:str