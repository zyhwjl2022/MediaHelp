from fastapi import APIRouter
from api.auth import router as auth_router
from api.douban import router as douban_router
from api.resource import router as resource_router
from api.sysSetting import router as sysSetting_router
api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(douban_router)
api_router.include_router(resource_router)
api_router.include_router(sysSetting_router)
