from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Text
from models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) 