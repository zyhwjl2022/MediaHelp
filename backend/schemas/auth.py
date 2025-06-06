from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str | None = None

class LoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名", example="admin")
    password: str = Field(..., description="密码", example="admin")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin"
            }
        } 