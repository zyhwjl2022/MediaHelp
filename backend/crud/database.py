from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from .config import settings
from models.base import Base

# 创建异步引擎
engine = create_async_engine(
    settings.database_config["async_url"],
    echo=settings.app_config["debug"]
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    异步数据库会话上下文管理器
    用法:
    async with get_db() as db:
        result = await db.execute(select(Model))
        items = result.scalars().all()
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的依赖函数
    用法:
    @app.get("/items/")
    async def read_items(db: AsyncSession = Depends(get_db_session)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    """
    async with get_db() as session:
        yield session 