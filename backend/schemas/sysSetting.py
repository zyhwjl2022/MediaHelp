from pydantic import BaseModel, Field
from typing import Optional

class SysSettingBase(BaseModel):
    """系统配置基础模型"""
    emby_url: str = Field(default="", description="Emby服务器地址")
    emby_api_key: str = Field(default="", description="Emby API密钥")
    alist_url: str = Field(default="", description="Alist服务器地址")
    alist_api_key: str = Field(default="", description="Alist API密钥")
    tianyiAccount: str = Field(default="", description="天翼账号")
    tianyiPassword: str = Field(default="", description="天翼密码")
    quarkCookie: str = Field(default="", description="夸克Cookie")

class SysSettingCreate(SysSettingBase):
    """创建系统配置模型"""
    pass

class SysSettingUpdate(SysSettingBase):
    """更新系统配置模型"""
    emby_url: Optional[str] = None
    emby_api_key: Optional[str] = None
    alist_url: Optional[str] = None
    alist_api_key: Optional[str] = None
    tianyiAccount: Optional[str] = None
    tianyiPassword: Optional[str] = None
    quarkCookie: Optional[str] = None

class SysSettingInDB(SysSettingBase):
    """数据库中的系统配置模型"""
    id: int
    
    class Config:
        from_attributes = True 