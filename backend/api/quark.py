from fastapi import APIRouter, Depends, Query, Body
from typing import List, Optional, Dict, Union, Tuple

import asyncio

from pydantic import BaseModel, Field
from api.deps import get_current_user
from models.user import User
from schemas.response import Response
from utils.quark_helper import QuarkHelper
from utils.config_manager import config_manager
from loguru import logger
from utils.down_load_to_fn import fn_os

router = APIRouter(prefix="/quark", tags=["夸克网盘"])

class QuarkFilePaths(BaseModel):
    """文件路径请求模型"""
    file_paths: List[str] = Field(default=[], description="文件路径列表")

class SaveShareFilesRequest(BaseModel):
    """保存分享文件请求模型"""
    share_url: str = Field(..., description="分享链接")
    stoken: str = Field(default="", description="分享token")
    target_dir: str = Field(default="0", description="目标文件夹ID")
    keyword: str = Field(default="ikan", description="关键词，用于创建新文件夹")
    pdir_fid: str = Field(default="0", description="来源文件夹ID")
    file_ids: List[str] = Field(default=[], description="要保存的文件ID列表，为空则保存所有文件")
    file_tokens: List[str] = Field(default=[], description="要保存的文件token列表，需要与file_ids一一对应")
    is_down_load: bool = Field(default=False, description="是否下载到本地")
    cloud_path: str = Field(default="", description="云盘路径")


class CreateDirectoryRequest(BaseModel):
    """创建文件夹请求模型"""
    name: str = Field(default="新建文件夹", description="文件夹名称")
    parent_id: str = Field(default="0", description="父文件夹ID")

class RenameFileRequest(BaseModel):
    """重命名文件请求模型"""
    file_id: str = Field(..., description="文件/文件夹ID")
    new_name: str = Field(..., description="新名称")

class DeleteFilesRequest(BaseModel):
    """删除文件请求模型"""
    file_ids: List[str] = Field(..., description="文件ID列表")

# 全局的 QuarkHelper 实例缓存
quark_helpers: Dict[str, QuarkHelper] = {}

async def get_quark_helper(user: User = Depends(get_current_user)) -> Tuple[Optional[QuarkHelper], Optional[Response]]:
    """
    获取用户的夸克助手实例
    :return: (helper, error_response) 元组，如果成功返回 (helper, None)，如果失败返回 (None, error_response)
    """
    try:
        if user.id not in quark_helpers or quark_helpers[user.id] is None:
            # 从系统配置中获取 cookie
            sys_config = config_manager.get_config()
            cookie = sys_config.get("quarkCookie", "")
            if not cookie:
                return None, Response(
                    code=400,
                    message="未配置夸克网盘 cookie，请在系统配置中添加 quark_cookie"
                )
                
            helper = QuarkHelper(cookie)
            if not await helper.init():
                return None, Response(
                    code=400,
                    message="夸克网盘初始化失败，请检查 cookie 是否有效"
                )
            quark_helpers[user.id] = helper
            
        return quark_helpers[user.id], None
    except Exception as e:
        logger.error(f"获取夸克助手实例失败: {str(e)}")
        return None, Response(
            code=-1,
            message=f"获取夸克助手实例失败: {str(e)}"
        )

@router.get("/files")
async def list_files(
    dir_id: str = Query(default="0", description="文件夹ID"),
    recursive: bool = Query(default=False, description="是否递归获取子文件夹"),
    user: User = Depends(get_current_user)
):
    """
    获取文件列表
    
    参数:
    - dir_id: 文件夹ID，默认为根目录
    - recursive: 是否递归获取子文件夹内容
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "list": [
                {
                    "fid": "文件ID",
                    "file_name": "文件名",
                    "file_type": 1,  // 1为文件夹，2为文件
                    "size": 1024,
                    "updated_at": "2024-01-01 12:00:00"
                }
            ]
        }
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        files = await helper.list_files(dir_id, recursive)
        return Response(
            code=200,
            message="操作成功",
            data={"list": files}
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return Response(code=-1, message=f"获取文件列表失败: {str(e)}")

@router.get("/search")
async def search_files(
    keyword: str = Query(..., description="搜索关键词"),
    dir_id: str = Query(default="0", description="搜索目录ID"),
    user: User = Depends(get_current_user)
):
    """
    搜索文件
    
    参数:
    - keyword: 搜索关键词
    - dir_id: 搜索目录ID，默认为根目录
    
    返回格式同 /files 接口
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        files = await helper.search(keyword, dir_id)
        return Response(
            code=200,
            message="操作成功",
            data={"list": files}
        )
    except Exception as e:
        logger.error(f"搜索文件失败: {str(e)}")
        return Response(code=-1, message=f"搜索文件失败: {str(e)}")

@router.get("/download/{file_id}")
async def get_download_info(
    file_id: str,
    user: User = Depends(get_current_user)
):
    """
    获取文件下载信息
    
    参数:
    - file_id: 文件ID
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "url": "下载链接",
            "filename": "文件名"
        }
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        info = await helper.get_download_info(file_id)
        if not info:
            return Response(code=404, message="文件不存在或无法获取下载信息")
        return Response(code=200, message="操作成功", data=info)
    except Exception as e:
        logger.error(f"获取下载信息失败: {str(e)}")
        return Response(code=-1, message=f"获取下载信息失败: {str(e)}")

@router.post("/directory")
async def create_directory(
    request: CreateDirectoryRequest,
    user: User = Depends(get_current_user)
):
    """
    创建文件夹
    
    参数:
    - name: 文件夹名称
    - parent_id: 父文件夹ID，默认为根目录
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "dir_id": "新建文件夹ID"
        }
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        dir_id = await helper.create_dir(request.name, request.parent_id)
        if not dir_id:
            return Response(code=400, message="创建文件夹失败")
        return Response(
            code=200,
            message="操作成功",
            data={"dir_id": dir_id}
        )
    except Exception as e:
        logger.error(f"创建文件夹失败: {str(e)}")
        return Response(code=-1, message=f"创建文件夹失败: {str(e)}")

@router.post("/rename")
async def rename_file(
    request: RenameFileRequest,
    user: User = Depends(get_current_user)
):
    """ 
    重命名文件或文件夹
    
    参数:
    - file_id: 文件/文件夹ID
    - new_name: 新名称
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        success = await helper.rename(request.file_id, request.new_name)
        if not success:
            return Response(code=400, message="重命名失败")
        return Response(code=200, message="操作成功")
    except Exception as e:
        logger.error(f"重命名失败: {str(e)}")
        return Response(code=-1, message=f"重命名失败: {str(e)}")

@router.delete("/files")
async def delete_files(
    delete_request: DeleteFilesRequest,
    user: User = Depends(get_current_user)
):
    """
    删除文件或文件夹
    
    参数:
    - file_ids: 单个文件ID或文件ID列表
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        success = await helper.delete(delete_request.file_ids)
        if not success:
            return Response(code=400, message="删除失败")
        return Response(code=200, message="操作成功")
    except Exception as e:
        logger.error(f"删除失败: {str(e)}")
        return Response(code=-1, message=f"删除失败: {str(e)}")

@router.post("/fids")
async def get_fids(
    file_paths: QuarkFilePaths,
    user: User = Depends(get_current_user)
):
    """
    获取文件路径对应的 fid
    
    参数:
    - file_paths: 文件路径列表，例如 ["/文件夹1", "/文件夹1/文件夹2"]
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": [
            {
                "file_path": "/文件夹1",
                "fid": "文件夹1的ID"
            },
            {
                "file_path": "/文件夹1/文件夹2",
                "fid": "文件夹2的ID"
            }
        ]
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
        fids = await helper.get_fids(file_paths.file_paths)
        return Response(
            code=200,
            message="操作成功",
            data=fids
        )
    except Exception as e:
        logger.error(f"获取文件ID失败: {str(e)}")
        return Response(code=-1, message=f"获取文件ID失败: {str(e)}")

@router.post("/share/save")
async def save_shared_files(
    request: SaveShareFilesRequest,
    user: User = Depends(get_current_user)
):
    """
    保存分享文件到网盘
    
    参数:
    - share_url: 分享链接
    - target_dir: 保存到的目标文件夹ID（可选）
    - file_ids: 要保存的文件ID列表，为空则保存所有文件
    - file_tokens: 要保存的文件token列表，需要与file_ids一一对应
    
    请求示例:
    ```json
    {
        "share_url": "https://pan.quark.cn/s/xxxxxx",
        "password": "1234",
        "target_dir": "0",
        "file_ids": ["file_id1", "file_id2"],
        "file_tokens": ["token1", "token2"]
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        # 解析分享链接
        share_info = helper.sdk.extract_share_info(request.share_url)
        if not share_info["share_id"]:
            return Response(code=400, message="无效的分享链接")
            
        # 获取分享信息
        share_response = await helper.sdk.get_share_info(
            share_info["share_id"], 
             share_info["password"]
        )
        
        if share_response.get("code") != 0:
            return Response(
                code=400, 
                message=share_response.get("message", "获取分享信息失败")
            )
            
        token = request.stoken
        if not token:
            return Response(code=400, message="获取分享token失败")
            
        # 如果没有指定要保存的文件，则获取所有文件
        if not request.file_ids:
            file_list = await helper.sdk.get_share_file_list(
                share_info["share_id"],
                token,
                request.pdir_fid if share_info["dir_id"] == '0' else share_info["dir_id"]
            )
            
            if file_list.get("code") != 0:
                return Response(
                    code=400, 
                    message=file_list.get("message", "获取分享文件列表失败")
                )
                
            files = file_list.get("data", {}).get("list", [])
            request.file_ids = [f["fid"] for f in files]
            request.file_tokens = [f.get("share_fid_token", "") for f in files]
            
        # 创建根文件夹
        target_list = await helper.list_files(request.target_dir)
        if target_list:
            found = False
            for item in target_list:
                if item.get('file_name') == request.keyword and item.get('dir'):
                    request.target_dir = item.get('fid')
                    found = True
                    break
            if not found:
                request.target_dir = await helper.create_dir(request.keyword, request.target_dir)
                if not request.target_dir:
                    return Response(code=400, message="创建目标文件夹失败")    

        # 保存文件
        save_response = await helper.sdk.save_share_files(
            share_info["share_id"],
            token,
            request.file_ids,
            request.file_tokens,
            request.target_dir,
            request.pdir_fid
        )
        
        if save_response.get("code") != 0:
            return Response(
                code=400, 
                message=save_response.get("message", "保存分享文件失败")
            )
        
        
        # 如果需要下载到本地文件夹
        if request.is_down_load:
            logger.info(f"开始下载分享文件到本地: {request.cloud_path}")
            fn_os.cloud_file_path = request.cloud_path+"/"+request.keyword
            fn_os.keyword = request.keyword
            fn_os.cloud_type = "quark"
            down_load_result,down_load_result_msg = await fn_os.run_async()
            if not down_load_result:
                return Response(code=500, message="下载失败,"+down_load_result_msg)

            
        return Response(code=200, message="操作成功", data=save_response.get("data",{}))
    except Exception as e:
        logger.error(f"保存分享文件失败: {str(e)}")
        return Response(code=-1, message=f"保存分享文件失败: {str(e)}")

@router.get("/share/info")
async def get_share_info(
    share_url: str = Query(..., description="分享链接"),
    password: str = Query(default="", description="分享密码"),
    user: User = Depends(get_current_user)
):
    """
    获取分享信息
    
    参数:
    - share_url: 分享链接
    - password: 分享密码（可选）
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "share_id": "分享ID",
            "token": "分享token",
            "share_name": "分享名称",
            "share_type": 1,  // 分享类型
            "created_at": "创建时间",
            "expired_at": "过期时间",
            "creator": {
                "name": "分享者名称"
            }
        }
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        # 解析分享链接
        share_info = helper.sdk.extract_share_info(share_url)
        if not share_info["share_id"]:
            return Response(code=400, message="无效的分享链接")
            
        # 获取分享信息
        share_response = await helper.sdk.get_share_info(
            share_info["share_id"], 
            password or share_info["password"]
        )
        
        if share_response.get("code") != 0:
            return Response(
                code=400, 
                message=share_response.get("message", "获取分享信息失败")
            )
            
        return Response(
            code=200,
            message="操作成功",
            data=share_response.get("data", {})
        )
    except Exception as e:
        logger.error(f"获取分享信息失败: {str(e)}")
        return Response(code=-1, message=f"获取分享信息失败: {str(e)}")

@router.get("/share/files")
async def get_share_files(
    share_url: str = Query(..., description="分享链接"),
    user: User = Depends(get_current_user)
):
    """
    获取分享文件列表
    
    参数:
    - share_url: 分享链接
    - password: 分享密码（可选）
    - dir_id: 文件夹ID，默认为根目录
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "list": [
                {
                    "fid": "文件ID",
                    "share_fid_token": "文件分享token",
                    "file_name": "文件名",
                    "file_type": 1,  // 1为文件夹，2为文件
                    "size": 1024,
                    "updated_at": "2024-01-01 12:00:00"
                }
            ],
            "share_info": {
                "share_id": "分享ID",
                "token": "分享token"
            }
        }
    }
    ```
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        # 解析分享链接
        share_info = helper.sdk.extract_share_info(share_url)
        if not share_info["share_id"]:
            return Response(code=400, message="无效的分享链接")
            
        # 获取分享信息
        try:    
            share_response = await helper.sdk.get_share_info(
                share_info["share_id"], 
                share_info["password"]
            )
        
            if share_response.get("code") != 0:
                return Response(
                    code=400, 
                    message=share_response.get("message", "获取分享信息失败：分享链接失效")
                )
        except Exception as e:
            logger.error(f"获取分享信息失败: {str(e)}")
            return Response(code=400, message=f"获取分享信息失败: 分享链接失效")
        
        token = share_response.get("data", {}).get("stoken")
        if not token:
                return Response(code=400, message="获取分享token失败")
        # 获取分享文件列表
        file_list = await helper.sdk.get_share_file_list(
            share_info["share_id"],
            token,
            share_info["dir_id"]
        )
        
        if file_list.get("code") != 0:
            return Response(
                code=400, 
                message=file_list.get("message", "获取分享文件列表失败")
            )
        return Response(
            code=200,
            message="操作成功",
            data={
                "list": file_list.get("data", {}).get("list", []),
                "paths": share_info["paths"],
                "share_info": {
                    "share_id": share_info["share_id"],
                    "token": token
                }
            }
        )
    except Exception as e:
        logger.error(f"获取分享文件列表失败: {str(e)}")
        return Response(code=-1, message=f"获取分享文件列表失败: {str(e)}") 