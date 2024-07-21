from pydantic import BaseModel, Field
from typing import Optional, Annotated
from pydantic.functional_validators import BeforeValidator


class UserBaseModel(BaseModel):
    full_name: Optional[str] = None
    username: str
    is_admin: bool = False

class User(UserBaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias="_id", default=None)

class UserInDB(UserBaseModel):
    hashed_password: bytes

class UserLogin(BaseModel):
    username: str
    plain_password: str
    
class UserCreate(UserBaseModel, UserLogin):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str