from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from ..models.user import UserRole


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.OPERATOR


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None