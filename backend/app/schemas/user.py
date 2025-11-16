from pydantic import BaseModel
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str


class TokenData(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
