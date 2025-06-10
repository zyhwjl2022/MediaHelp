from fastapi import APIRouter, Depends, Query
from typing import Any, Dict, List, Optional
from api.deps import get_current_user
from models.user import User
from schemas.response import Response
from utils.tg_resource_sdk import tg_resource, SearchResult, ResourceItem, ChannelInfo

router = APIRouter(prefix="/tg-resource", tags=["TG资源"])

@router.get("/search", response_model=Response[Dict[str, List[SearchResult]]])
async def search_resources(
    keyword: str = Query(default="", description="搜索关键词"),
    channel_id: Optional[str] = Query(default=None, description="频道ID（可选）"),
    message_id: Optional[str] = Query(default=None, description="消息ID（可选，用于分页）"),
    current_user: User = Depends(get_current_user)
):
    """
    搜索TG资源
    
    参数:
    - keyword: 搜索关键词
    - channel_id: 指定频道ID（可选）
    - message_id: 指定消息ID（可选，用于分页）
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "data": [
                {
                    "list": [
                        {
                            "messageId": "123",
                            "title": "资源标题",
                            "completeTitle": null,
                            "link": null,
                            "pubDate": "2024-03-21T10:00:00Z",
                            "content": "资源描述",
                            "description": null,
                            "image": "https://example.com/image.jpg",
                            "cloudLinks": [
                                "https://pan.example.com/xxx"
                            ],
                            "tags": ["#资源", "#电影"],
                            "cloudType": "aliyun",
                            "channel": "频道名称",
                            "channelId": "channel123"
                        }
                    ],
                    "channelInfo": {
                        "id": "channel123",
                        "name": "频道名称",
                        "channelLogo": "https://example.com/logo.jpg"
                    },
                    "id": "channel123"
                }
            ]
        }
    }
    ```
    
    说明:
    1. 如果不指定 channel_id，将搜索所有已配置的频道
    2. 可以通过 message_id 参数实现分页，获取指定消息之前的内容
    3. 返回的资源列表按时间倒序排列
    4. 只返回包含云盘链接的消息
    5. cloudType 表示云盘类型，支持：
       - aliyun: 阿里云盘
       - tianyiyun: 天翼云盘
       - quark: 夸克网盘
       - baidu: 百度网盘
    """
    result = await tg_resource.search_all(
        keyword=keyword,
        channel_id=channel_id,
        message_id=message_id
    )
    return Response(data=result)

@router.get("/config", response_model=Response[Dict[str, Any]])
async def get_resource_config(
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
    config = tg_resource._get_config()
    return Response(data=config)

@router.put("/config", response_model=Response)
async def update_resource_config(
    channels: Optional[List[Dict[str, str]]] = None,
    patterns: Optional[Dict[str, str]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    更新TG资源配置
    
    参数:
    - channels: 频道列表，格式：[{"id": "频道ID", "name": "频道名称"}]
    - patterns: 云盘链接匹配模式，格式：{"aliyun": "正则表达式"}
    
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
    await tg_resource.update_config(channels, patterns)
    return Response(message="配置更新成功") 