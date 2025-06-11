from fastapi import APIRouter, Depends, Query, Body
from typing import List, Optional, Dict, Any, Union, Tuple
from api.deps import get_current_user
from models.user import User
from schemas.response import Response
from utils.quark_helper import QuarkHelper
from utils.config_manager import config_manager
from loguru import logger

router = APIRouter(prefix="/quark", tags=["夸克网盘"])

# 全局的 QuarkHelper 实例缓存
quark_helpers: Dict[str, QuarkHelper] = {}

async def get_quark_helper(user: User = Depends(get_current_user)) -> Tuple[Optional[QuarkHelper], Optional[Response]]:
    """
    获取用户的夸克助手实例
    :return: (helper, error_response) 元组，如果成功返回 (helper, None)，如果失败返回 (None, error_response)
    """
    try:
        if user.id not in quark_helpers:
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
    name: str = Body(..., description="文件夹名称"),
    parent_id: str = Body(default="0", description="父文件夹ID"),
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
            
        dir_id = await helper.create_dir(name, parent_id)
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

@router.put("/rename")
async def rename_file(
    file_id: str = Body(..., description="文件/文件夹ID"),
    new_name: str = Body(..., description="新名称"),
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
            
        success = await helper.rename(file_id, new_name)
        if not success:
            return Response(code=400, message="重命名失败")
        return Response(code=200, message="操作成功")
    except Exception as e:
        logger.error(f"重命名失败: {str(e)}")
        return Response(code=-1, message=f"重命名失败: {str(e)}")

@router.delete("/files")
async def delete_files(
    file_ids: Union[str, List[str]] = Body(..., description="文件ID或ID列表"),
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
            
        success = await helper.delete(file_ids)
        if not success:
            return Response(code=400, message="删除失败")
        return Response(code=200, message="操作成功")
    except Exception as e:
        logger.error(f"删除失败: {str(e)}")
        return Response(code=-1, message=f"删除失败: {str(e)}")

@router.post("/share/save")
async def save_shared_files(
    share_url: str = Body(..., description="分享链接"),
    password: str = Body(default="", description="分享密码"),
    target_dir: str = Body(default="0", description="目标文件夹ID"),
    user: User = Depends(get_current_user)
):
    """
    保存分享文件到网盘
    
    参数:
    - share_url: 分享链接
    - password: 分享密码（可选）
    - target_dir: 保存到的目标文件夹ID（可选）
    """
    try:
        helper, error = await get_quark_helper(user)
        if error:
            return error
            
        success = await helper.save_shared_files(share_url, password, target_dir)
        if not success:
            return Response(code=400, message="保存分享文件失败")
        return Response(code=200, message="操作成功")
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
    password: str = Query(default="", description="分享密码"),
    dir_id: str = Query(default="0", description="文件夹ID"),
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
        share_response = await helper.sdk.get_share_info(
            share_info["share_id"], 
            password or share_info["password"]
        )
        
        if share_response.get("code") != 0:
            return Response(
                code=400, 
                message=share_response.get("message", "获取分享信息失败")
            )
        token = share_response.get("data", {}).get("stoken")
        if not token:
            return Response(code=400, message="获取分享token失败")
            
        # 获取分享文件列表
        file_list = await helper.sdk.get_share_file_list(
            share_info["share_id"],
            token,
            dir_id or share_info["dir_id"]
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
                "share_info": {
                    "share_id": share_info["share_id"],
                    "token": token
                }
            }
        )
    except Exception as e:
        logger.error(f"获取分享文件列表失败: {str(e)}")
        return Response(code=-1, message=f"获取分享文件列表失败: {str(e)}") 