from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from schemas.response import ErrorResponse

class APIException(HTTPException):
    """自定义API异常"""
    def __init__(
        self,
        code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "请求错误",
        detail: Optional[str] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(status_code=code, detail=detail)

def create_error_response(
    *,
    code: int,
    message: str,
    detail: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
) -> Dict[str, Any]:
    """创建错误响应"""
    return ErrorResponse(
        code=code,
        message=message,
        detail=detail,
        path=path,
        method=method,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ).model_dump()


async def api_exception_handler(request: Any, exc: APIException) -> JSONResponse:
    """处理自定义API异常"""
    return JSONResponse(
        status_code=exc.code,
        content=create_error_response(
            code=exc.code,
            message=exc.message,
            detail=str(exc.detail) if exc.detail else None,
            path=str(request.url),
            method=request.method,
        ),
    )

async def validation_exception_handler(request: Any, exc: RequestValidationError) -> JSONResponse:
    """处理请求参数验证异常"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="请求参数验证错误",
            detail=str(exc),
            path=str(request.url),
            method=request.method,
        ),
    )

async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=exc.status_code,
            message=str(exc.detail),
            path=str(request.url),
            method=request.method,
        ),
    ) 