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
    description: str | None = None
    likes: list[str] | None = None
    dislikes: list[str] | None = None
    hobbies: list[str] | None = None
    profile_picture: str | None = None


class config:
        orm_mode = True