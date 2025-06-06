from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., description="用户名", example="newuser")
    email: EmailStr = Field(..., description="电子邮箱", example="newuser@example.com")
    is_active: bool = Field(default=True, description="是否激活")

class UserCreate(UserBase):
    password: str = Field(..., description="密码", example="password123")

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 