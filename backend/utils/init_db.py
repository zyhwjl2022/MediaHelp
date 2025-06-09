import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from crud.database import get_db
from crud.user import user as user_crud
from crud.sysSetting import sys_setting
from schemas.user import UserCreate
from schemas.sysSetting import SysSettingCreate
from models.base import Base
from crud.database import engine

async def init_db() -> None:
    """初始化数据库"""
    try:
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 创建默认管理员用户
        async with get_db() as db:
            # 检查是否已存在管理员用户
            admin_user = await user_crud.get_by_username(db, username="admin")
            if not admin_user:
                admin = UserCreate(
                    username="admin",
                    email="admin@example.com",
                    password="admin",
                    is_active=True
                )
                await user_crud.create(db, obj_in=admin)
                print("默认管理员用户已创建")
            else:
                print("管理员用户已存在")

            # 创建系统设置
            setting = await sys_setting.get_by(db, id=1)
            if not setting:
                default_setting = SysSettingCreate(
                    emby_url="",
                    emby_api_key="",
                    alist_url="",
                    alist_api_key="",
                    tianyiAccount="",
                    tianyiPassword="",
                    quarkCookie=""
                )
                # 手动设置 id 为 1
                db_obj = sys_setting.model(id=1, **default_setting.model_dump())
                db.add(db_obj)
                await db.commit()
                print("默认系统设置已创建")
            else:
                print("系统设置已存在")

    except Exception as e:
        print(f"初始化数据库时出错: {str(e)}")
        raise

def init_database():
    """同步函数调用异步初始化"""
    asyncio.run(init_db()) 