import http
import sys
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from loguru import logger
import logging
from crud.config import settings
from api.main import api_router
from utils.exceptions import APIException, api_exception_handler, validation_exception_handler, http_exception_handler, create_error_response
from datetime import datetime

def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 避免重复日志
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    # 移除所有默认的处理器
    logging.getLogger().handlers = []
    
    # 配置loguru - 使用loguru的时间格式
    logger.configure(
        handlers=[{
            "sink": sys.stdout,
            "level": settings.logging_config["level"],
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        }]
    )
    
    # 拦截所有标准库的日志
    logging.getLogger().addHandler(InterceptHandler())
    
    # 特别处理uvicorn的日志
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = []
        _logger.propagate = False
        _logger.addHandler(InterceptHandler())

def init_app():
    # 初始化日志
    setup_logging()
    
    # 初始化 FastAPI 应用
    app = FastAPI(
        title=settings.app_config["title"],
        description=settings.app_config["description"],
        version=settings.app_config["version"],
        debug=settings.app_config["debug"],
        generate_unique_id_function=custom_generate_unique_id,
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册异常处理器
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    app.include_router(api_router, prefix=settings.app_config["API_V1_STR"])
    return app

app = init_app()

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, e: Exception):
    logger.error(f"请求路径: {request.url}\n请求方法: {request.method}\n错误信息: {str(e)}")
    return JSONResponse(
        status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        content=create_error_response(
            code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            message="发生了一个内部错误，请稍后再试。",
            detail=str(e),
            path=str(request.url),
            method=request.method
        )
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_config["host"],
        port=settings.server_config["port"],
        reload=settings.app_config["debug"]
    )
