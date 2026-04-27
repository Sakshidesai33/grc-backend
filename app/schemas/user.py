from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    department: str = "General"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: EmailStr  # OAuth2PasswordRequestForm uses 'username'
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
