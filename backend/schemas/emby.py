from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class EmbyItemResponse(BaseModel):
    """Emby 媒体项目响应模型"""
    Items: List[Dict[str, Any]]
    TotalRecordCount: int
    
    class Config:
        from_attributes = True

class SyncJobCreate(BaseModel):
    """创建同步任务请求模型"""
    target_id: str
    item_ids: List[str]
    quality: Optional[str] = None
    parent_id: Optional[str] = None
    unwatched_only: bool = False
    sync_new_content: bool = False
    item_limit: Optional[int] = None

    class Config:
        from_attributes = True

class SyncJobResponse(BaseModel):
    """同步任务响应模型"""
    Id: str
    TargetId: str
    ItemIds: List[str]
    Quality: Optional[str]
    Status: str
    Progress: Optional[float]
    
    class Config:
        from_attributes = True

class SyncJobStatus(BaseModel):
    """同步任务状态模型"""
    Id: str
    Status: str
    Progress: Optional[float]
    LastResult: Optional[str]
    
    class Config:
        from_attributes = True

class SyncJobItems(BaseModel):
    """同步任务项目列表模型"""
    Items: List[Dict[str, Any]]
    TotalRecordCount: int
    
    class Config:
        from_attributes = True