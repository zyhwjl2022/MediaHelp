from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from models.base import BaseModel


class SysSetting(BaseModel):
    __tablename__ = "sys_setting"

    emby_url: Mapped[str] = mapped_column(String(255), nullable=False)
    emby_api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    alist_url: Mapped[str] = mapped_column(String(255), nullable=False)
    alist_api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    tianyiAccount: Mapped[str] = mapped_column(String(255), nullable=False)
    tianyiPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    
    quarkCookie: Mapped[str] = mapped_column(String(255), nullable=False)

