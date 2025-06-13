"""天翼云盘类型定义"""

from typing import TypedDict, List, Optional, Dict, Any, Union
from datetime import datetime

class CapacityInfo(TypedDict):
    freeSize: int
    totalSize: int
    usedSize: int

class UserInfo(TypedDict):
    """用户信息"""
    account: str
    cloudCapacityInfo: CapacityInfo
    familyCapacityInfo: CapacityInfo

class CapacityInfo(TypedDict):
    """容量信息"""
    total_size: int  # 总空间，单位KB
    used_size: int   # 已使用空间，单位KB
    free_size: int   # 剩余空间，单位KB

class UserSizeInfo(TypedDict):
    """用户容量信息"""
    cloud_capacity_info: CapacityInfo  # 个人容量信息
    family_capacity_info: CapacityInfo  # 家庭容量信息

class FileInfo(TypedDict):
    """文件信息"""
    fileId: str  # 文件ID，对应API返回的id
    fileName: str  # 文件名，对应API返回的name
    fileType: str  # 文件类型，对应API返回的mediaType
    fileSize: int  # 文件大小，对应API返回的size
    lastOpTime: str  # 最后操作时间
    parentId: str  # 父文件夹ID，对应API返回的pdir_fid
    path: str  # 文件路径
    icon: Dict[str, str]  # 文件图标
    createDate: str  # 创建时间
    fileCata: int  # 文件分类
    mediaType: int  # 媒体类型
    md5: Optional[str]  # 文件MD5
    rev: Optional[str]  # 文件版本
    starLabel: Optional[int]  # 星标标记

class ShareInfo(TypedDict):
    """分享信息"""
    shareId: str
    shareName: str
    shareMode: str
    expireTime: str
    shareUrl: str
    creator: Dict[str, str]
    fileCount: int
    accessCode: Optional[str]

class BatchTaskInfo(TypedDict):
    """批量任务信息"""
    fileId: str
    fileName: str
    isFolder: bool
    md5: Optional[str]

class SaveShareResult(TypedDict):
    """保存分享文件结果"""
    message: str
    task_id: str
    status: Dict[str, Any]
    failed_files: Optional[List[BatchTaskInfo]]
    failed_count: Optional[int]

class ShareSaveTaskParams(TypedDict):
    """保存分享文件任务参数"""
    type: str
    taskInfos: List[BatchTaskInfo]
    targetFolderId: str
    shareId: str

class ApiResponse(TypedDict):
    """API响应"""
    res_code: Union[int, str]
    res_msg: Optional[str]
    data: Optional[Any]

class FileListResponse(ApiResponse):
    """文件列表响应"""
    fileListAO: Dict[str, Any]

class ShareListResponse(ApiResponse):
    """分享文件列表响应"""
    fileListAO: Dict[str, Any]
    shareInfo: ShareInfo

class TaskResponse(ApiResponse):
    """任务响应"""
    taskId: str
    status: int

class DownloadInfo(TypedDict):
    """下载信息"""
    url: str
    fileId: str
    fileName: str
    size: int
    expire: datetime

class UploadInfo(TypedDict):
    """上传信息"""
    uploadUrl: str
    uploadFileId: str
    uploadToken: str
    expire: datetime

class ConflictInfo(TypedDict):
    """文件冲突信息"""
    fileId: str
    fileName: str
    conflictType: int  # 1: 重名, 2: 已存在
    resolution: Optional[str]  # rename, skip, overwrite

class ShareSaveInfo(TypedDict):
    """分享保存信息"""
    shareId: str
    fileIds: List[str]
    targetFolderId: str
    accessCode: Optional[str]

class BatchTaskParams(TypedDict):
    """批量任务参数"""
    type: str
    taskInfos: List[Dict[str, Any]]
    targetFolderId: Optional[str]

class LoginFormCache(TypedDict):
    """登录表单缓存"""
    captcha_token: str
    req_id: str
    lt: str
    param_id: str

class TokenSession(TypedDict):
    """会话信息"""
    res_code: int
    res_message: str
    access_token: str
    family_session_key: str
    family_session_secret: str
    refresh_token: str
    login_name: str
    session_key: str

class RefreshTokenSession(TypedDict):
    """刷新令牌会话"""
    expires_in: int
    access_token: str
    refresh_token: str

class ClientSession(TypedDict):
    """客户端会话"""
    access_token: str
    session_key: str

class ConfigurationOptions(TypedDict):
    """客户端配置选项"""
    username: Optional[str]
    password: Optional[str]
    sson_cookie: Optional[str] 