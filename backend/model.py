from typing import List, Optional
from pydantic import BaseModel


class UserOut(BaseModel):
    username : str
    email: str


class UserRegister(UserOut):
   password: str


class UserLogin(BaseModel):
    username : str
    password: str



class UserProfileSchema(BaseModel):
    user_id: int
    description: Optional[str] = None
    likes: Optional[List[str]] = None
    dislikes: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    profile_picture: Optional[str] = None


class config:
        orm_mode = True