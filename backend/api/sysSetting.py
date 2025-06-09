from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from crud.database import get_db_session
from models.user import User
from crud.sysSetting import sys_setting
from schemas.sysSetting import SysSettingUpdate
from utils.sys_config import global_config

router = APIRouter(prefix="/sysSetting", tags=["系统设置"])

@router.get("/config")
async def get_system_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统配置"""
    # 优先从缓存获取
    cached_config = global_config.get_config()
    if cached_config:
        return cached_config
    
    # 缓存不存在，从数据库获取并更新缓存
    config = await sys_setting.get_sys_setting(db)
    global_config.update_config(config)
    return global_config.get_config()

@router.put("/config")
async def update_system_config(
    config: SysSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新系统配置"""
    # 更新数据库
    updated_config = await sys_setting.update_sys_setting(db, obj_in=config)
    # 更新缓存
    global_config.update_config(updated_config)
    return global_config.get_config()




