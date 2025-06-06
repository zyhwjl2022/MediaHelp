# crud/user.py
from typing import Optional
from sqlalchemy.orm import Session
from crud.base import CRUDBase
from models.user import User
from schemas.user import UserCreate, UserUpdate
from utils.auth import verify_password, get_password_hash

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    # 可以添加用户特定的方法
    async def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return await self.get_by(db, email=email)

    async def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return await self.get_by(db, username=username)

    async def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """创建新用户"""
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

user = CRUDUser(User)