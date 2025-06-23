import os
from typing import List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from crud.config import settings

class AuthCodeMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        protected_paths: List[str] = None,
        excluded_paths: List[str] = None
    ):
        super().__init__(app)
        self.protected_paths = protected_paths or []
        self.excluded_paths = excluded_paths or []
        # 从环境变量获取授权码，如果没有则从配置文件获取
        self.auth_code = os.getenv("AUTH_CODE") or settings.security_config.get("auth_code")

    async def dispatch(self, request: Request, call_next):
        # 如果没有设置授权码，则不进行验证
        if not self.auth_code:
            return await call_next(request)

        # 检查是否是受保护的路径
        path = request.url.path
        is_protected = any(path.startswith(p) for p in self.protected_paths)
        is_excluded = any(path.startswith(p) for p in self.excluded_paths)

        if is_protected and not is_excluded:
            # 从请求头或查询参数中获取授权码
            request_auth_code = request.headers.get("X-Auth-Code")
            if not request_auth_code:
                request_auth_code = request.query_params.get("auth_code")

            if not request_auth_code:
                raise HTTPException(
                    status_code=401,
                    detail="未提供授权码"
                )

            if request_auth_code != self.auth_code:
                raise HTTPException(
                    status_code=401,
                    detail="授权码无效"
                )

        return await call_next(request)