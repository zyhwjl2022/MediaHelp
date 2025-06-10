from fastapi import APIRouter, Depends
from api.deps import get_current_user
from models.user import User
from schemas.response import Response
from schemas.sysSetting import SysSettingUpdate, TGChannel, TGResourceConfig
from utils.config_manager import config_manager
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/sysSetting", tags=["系统设置"])

@router.get("/config", response_model=Response[Dict[str, Any]])
async def get_system_config(current_user: User = Depends(get_current_user)):
    """
    获取系统配置
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "emby_url": "http://emby.example.com",
            "emby_api_key": "your-api-key",
            "alist_url": "http://alist.example.com",
            "alist_api_key": "your-api-key",
            "tianyiAccount": "your-account",
            "tianyiPassword": "your-password",
            "quarkCookie": "your-cookie"
        }
    }
    ```
    """
    config = config_manager.get_config()
    return Response(data=config)

@router.put("/config", response_model=Response[Dict[str, Any]])
async def update_system_config(
    config: SysSettingUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新系统配置
    
    请求示例:
    ```json
    {
        "emby_url": "http://emby.example.com",
        "emby_api_key": "your-api-key",
        "alist_url": "http://alist.example.com",
        "alist_api_key": "your-api-key",
        "tianyiAccount": "your-account",
        "tianyiPassword": "your-password",
        "quarkCookie": "your-cookie"
    }
    ```
    """
    # 更新配置文件
    new_config = {}
    if config.emby_url is not None:
        new_config["emby_url"] = config.emby_url
    if config.emby_api_key is not None:
        new_config["emby_api_key"] = config.emby_api_key
    if config.alist_url is not None:
        new_config["alist_url"] = config.alist_url
    if config.alist_api_key is not None:
        new_config["alist_api_key"] = config.alist_api_key
    if config.tianyiAccount is not None:
        new_config["tianyiAccount"] = config.tianyiAccount
    if config.tianyiPassword is not None:
        new_config["tianyiPassword"] = config.tianyiPassword
    if config.quarkCookie is not None:
        new_config["quarkCookie"] = config.quarkCookie
        
    config_manager.update_config(new_config)
    
    # 返回更新后的配置
    updated_config = config_manager.get_config()
    return Response(data=updated_config)

@router.get("/tg-resource/config", response_model=Response[TGResourceConfig])
async def get_tg_resource_config(
    current_user: User = Depends(get_current_user)
):
    """
    获取TG资源配置
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "telegram": {
                "baseUrl": "https://t.me/s",
                "channels": [
                    {"id": "ailaoban", "name": "AI老班"},
                    {"id": "ailiaoba", "name": "AI聊吧"}
                ]
            },
            "cloudPatterns": {
                "aliyun": "https?://www\\.aliyundrive\\.com/s/[a-zA-Z0-9]+",
                "tianyiyun": "https?://cloud\\.189\\.cn/web/share\\?code=[a-zA-Z0-9]+"
            }
        }
    }
    ```
    """
    config = config_manager.get_config()
    return Response(data=config.get("tg_resource", {}))

@router.put("/tg-resource/config", response_model=Response)
async def update_tg_resource_config(
    channels: Optional[List[TGChannel]] = None,
    patterns: Optional[Dict[str, str]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    更新TG资源配置
    
    参数:
    - channels: 频道列表
    - patterns: 云盘链接匹配模式
    
    示例:
    ```json
    {
        "channels": [
            {"id": "ailaoban", "name": "AI老班"},
            {"id": "ailiaoba", "name": "AI聊吧"}
        ],
        "patterns": {
            "aliyun": "https?://www\\.aliyundrive\\.com/s/[a-zA-Z0-9]+",
            "tianyiyun": "https?://cloud\\.189\\.cn/web/share\\?code=[a-zA-Z0-9]+"
        }
    }
    ```
    """
    config = config_manager.get_config()
    tg_config = config.get("tg_resource", {})
    
    if channels is not None:
        tg_config["telegram"]["channels"] = [channel.dict() for channel in channels]
    if patterns is not None:
        tg_config["cloudPatterns"] = patterns
    
    config_manager.update_config({"tg_resource": tg_config})
    return Response(message="TG资源配置更新成功")






