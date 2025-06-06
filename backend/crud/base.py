from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 定义泛型类型变量
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD 对象初始化
        :param model: SQLAlchemy 模型类
        """
        self.model = model

    async def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        通过 ID 获取对象
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个对象
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建对象
        """
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新对象
        """
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        删除对象
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def exists(self, db: Session, id: Any) -> bool:
        """
        检查对象是否存在
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_by(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        通过字段获取对象
        """
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    def count(self, db: Session) -> int:
        """
        获取对象总数
        """
        return db.query(self.model).count()

    def filter_by(self, db: Session, **kwargs) -> List[ModelType]:
        """
        按条件过滤对象
        """
        return db.query(self.model).filter_by(**kwargs).all()

    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[ModelType]:
        """
        通过字段获取对象
        """
        return db.query(self.model).filter(getattr(self.model, field) == value).first() 