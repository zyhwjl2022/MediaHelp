from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.sysSetting import SysSetting
from crud.base import CRUDBase
from schemas.sysSetting import SysSettingCreate, SysSettingUpdate

class SysSettingCRUD(CRUDBase[SysSetting, SysSettingCreate, SysSettingUpdate]):
    def __init__(self):
        super().__init__(SysSetting)

    async def get_sys_setting(self, db: AsyncSession) -> SysSetting:
        """获取系统配置，如果不存在则创建默认配置"""
        query = select(self.model)
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            # 创建默认配置
            default_setting = SysSettingCreate(
                emby_url="",
                emby_api_key="",
                alist_url="",
                alist_api_key="",
                tianyiAccount="",
                tianyiPassword="",
                quarkCookie=""
            )
            setting = await self.create(db, obj_in=default_setting)
        
        return setting

    async def update_sys_setting(self, db: AsyncSession, *, obj_in: SysSettingUpdate) -> SysSetting:
        """更新系统配置"""
        setting = await self.get_sys_setting(db)
        return await self.update(db, db_obj=setting, obj_in=obj_in)

sys_setting = SysSettingCRUD()

