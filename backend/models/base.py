from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Integer

def get_utc_now():
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class BaseModel(Base):
    """
    基础模型类，包含ID和时间戳
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now) 