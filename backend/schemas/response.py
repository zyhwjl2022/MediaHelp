from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ResponseBase(BaseModel):
    """基础响应模型"""
    code: int = 200
    message: str = "操作成功"

class Response(ResponseBase, Generic[T]):
    """通用响应模型"""
    data: Optional[T] = None

class ErrorResponse(ResponseBase):
    """错误响应模型"""
    code: int = 400
    message: str
    detail: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    timestamp: Optional[str] = None 