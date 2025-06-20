"""天翼云盘API接口"""

import asyncio
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.deps import get_current_user
from models.user import User
from schemas.response import Response
from utils.cloud189.client import Cloud189Client
from utils.cloud189.types import FileInfo, ShareInfo
from utils.cloud189.error import Cloud189Error
from utils.config_manager import config_manager

router = APIRouter(
    prefix="/cloud189",
    tags=["cloud189"]
)

# 请求模型定义
class Cloud189Config(BaseModel):
    """天翼云盘配置"""
    username: Optional[str] = None
    password: Optional[str] = None
    cookies: Optional[str] = None
    sson_cookie: Optional[str] = None

class FileListRequest(BaseModel):
    """文件列表请求"""
    folder_id: str = "-11"

class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str

class CreateFolderRequest(BaseModel):
    """创建文件夹请求"""
    folder_name: str
    parent_id: str = "-11"

class RenameRequest(BaseModel):
    """重命名请求"""
    file_id: str
    new_name: str

class DeleteRequest(BaseModel):
    """删除请求"""
    file_ids: List[str]

class ShareRequest(BaseModel):
    """分享请求"""
    share_url: str
    access_code: Optional[str] = None

class SaveShareRequest(BaseModel):
    """保存分享文件请求"""
    share_url: str
    target_folder_id: str = "-11"
    file_ids: Optional[List[Any]] = None

class ShareFilesRequest(BaseModel):
    """获取分享文件列表请求"""
    share_url: str
    access_code: Optional[str] = None
    file_id: Optional[str] = None

class DeleteFilesRequest(BaseModel):
    """删除文件请求"""
    file_ids: List[Dict[str, Any]]

# 客户端缓存
_client_cache: Optional[Cloud189Client] = None

async def get_client() -> Cloud189Client:
    """获取客户端实例"""
    global _client_cache
    
    if not _client_cache:
        # 从系统配置中获取账号信息
        sys_config = config_manager.get_config()
        username = sys_config.get("tianyiAccount", "")
        password = sys_config.get("tianyiPassword", "")
        
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="未配置天翼云盘账号，请在系统配置中添加 tianyiAccount 和 tianyiPassword"
            )
            
        _client_cache = Cloud189Client(
            username=username,
            password=password
        )
        if not await _client_cache.login():
            raise HTTPException(status_code=500, detail="天翼云盘登录失败")
            
    return _client_cache

@router.post("/init")
async def init_client(
    current_user: User = Depends(get_current_user)
):
    """初始化客户端"""
    try:
        # 从系统配置中获取账号信息
        sys_config = config_manager.get_config()
        username = sys_config.get("cloud189Account", "")
        password = sys_config.get("cloud189Password", "")
        
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="未配置天翼云盘账号，请在系统配置中添加 cloud189Account 和 cloud189Password"
            )
            
        client = Cloud189Client(
            username=username,
            password=password
        )
        if not await client.login():
            raise HTTPException(status_code=4001, detail="登录失败")
            
        global _client_cache
        _client_cache = client
        
        return {"message": "初始化成功", "user_info": client.user_info}
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/files")
async def list_files(
    req: FileListRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
) -> Response[Any]:
    """获取文件列表"""
    try:
        result = await client.list_files(req.folder_id)
        return Response(data=result)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search")
async def search_files(
    req: SearchRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
) -> List[FileInfo]:
    """搜索文件"""
    try:
        result = await client.search_files(req.keyword)
        return result.get("fileListAO", {}).get("fileList", [])
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/download")
async def get_download_url(
    file_id: str,
    share_id: Optional[str] = None,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
) -> str:
    """获取下载链接"""
    try:
        return await client.get_download_url(file_id, share_id)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/folder")
async def create_folder(
    req: CreateFolderRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
):
    """创建文件夹"""
    try:
        res = await client.create_folder(req.folder_name, req.parent_id)
        return Response(data = res)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rename")
async def rename_file(
    req: RenameRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
):
    """重命名文件"""
    try:
        res = await client.rename_file(req.file_id, req.new_name)
        return Response(data = res)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/share/info")
async def get_share_info(
    req: ShareRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
) -> ShareInfo:
    """获取分享信息"""
    try:
        # 解析分享链接
        url, code = client.parse_cloud_share(req.share_url)
        if not url:
            raise HTTPException(status_code=400, detail="无效的分享链接")
            
        # 使用提供的访问码或从链接中解析的访问码
        access_code = req.access_code or code
        
        # 获取分享码
        share_code = client.parse_share_code(url)
        
        # 如果有访问码，先验证
        if access_code:
            await client.check_access_code(share_code, access_code)
            
        # 获取分享信息
        return await client.get_share_info(share_code)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/share/save")
async def save_shared_files(
    req: SaveShareRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
):
    """保存分享文件"""
    try:
        result = await client.save_share_files(
            share_url=req.share_url,
            target_folder_id=req.target_folder_id,
            file_ids=req.file_ids
        )
        return Response(data=result)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/share/files")
async def list_share_files(
    req: ShareFilesRequest,
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
) -> Response[Any]:
    """获取分享文件列表"""
    try:
        # 解析分享链接
        logger.info(f"解析分享链接: {req.share_url}")
        url = client.parse_cloud_share(req.share_url)
        if not url:
            raise HTTPException(status_code=400, detail="无效的分享链接")
            
        # 获取分享码
        share_code = client.parse_share_code(url)
        
        # 获取分享信息
        share_info = await client.get_share_info(share_code)
        
        # 获取文件列表
        files = await client.list_share_files(
            share_id=share_info["shareId"],
            file_id= req.file_id or share_info["fileId"],
            share_mode=share_info.get("shareMode", "1"),
            access_code=share_info.get("accessCode", ""),
            is_folder=share_info.get("isFolder", "")
        )
        
        return Response(data=files)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str('获取分享文件列表失败,分享链接失效'))

@router.post("/delete")
async def delete_files(
    request: DeleteFilesRequest, 
    client: Cloud189Client = Depends(get_client),
    current_user: User = Depends(get_current_user)
):
    """
    删除文件或文件夹
    :param request: 删除文件请求
    :param client: 天翼云盘客户端
    """
    try:
        result = await client.delete_files(request.file_ids)
        return Response(code=200, message=result["message"], data=result)
    except Cloud189Error as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}") 