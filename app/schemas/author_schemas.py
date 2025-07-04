 

from pydantic import (
 
    BaseModel,
    ConfigDict,
 
)







class AuthorDescription(BaseModel):
    description: str 
    model_config = ConfigDict(extra="forbid")


class AuthorDescriptionResponse(BaseModel):
    success:str