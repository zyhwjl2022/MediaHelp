from fastapi import APIRouter
from api.auth import router as auth_router
from api.douban import router as douban_router
from api.sysSetting import router as sysSetting_router
from api.notify import router as notify_router
from api.tg_resource import router as tg_resource_router
from api import proxy
from api.quark import router as quark_router
from api.cloud189 import router as cloud189_router
api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(douban_router)
api_router.include_router(sysSetting_router)
api_router.include_router(notify_router)
api_router.include_router(tg_resource_router)
api_router.include_router(quark_router)
api_router.include_router(cloud189_router)

# 注册代理服务路由
api_router.include_router(proxy.router)
