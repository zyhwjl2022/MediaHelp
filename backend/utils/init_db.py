import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from crud.database import get_db
from crud.user import user as user_crud
from schemas.user import UserCreate
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

    except Exception as e:
        print(f"初始化数据库时出错: {str(e)}")
        raise

def init_database():
    """同步函数调用异步初始化"""
    asyncio.run(init_db()) 