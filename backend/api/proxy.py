from fastapi import APIRouter, Response, HTTPException
from utils.http_client import http_client
import base64
from urllib.parse import unquote
from loguru import logger
import aiohttp

router = APIRouter(prefix="/proxy", tags=["代理服务"])

@router.get("/image_proxy")
async def proxy_image(url: str):
    """
    代理图片请求
    
    参数:
    - url: base64编码的原始图片URL
    
    返回:
    - 图片内容
    """
    try:
        # 解码URL
        try:
            # 使用 urlsafe_b64decode 来解码
            decoded_url = unquote(base64.urlsafe_b64decode(url).decode('utf-8'))
        except Exception as e:
            logger.error(f"URL解码失败: {str(e)}")
            raise HTTPException(status_code=400, detail="无效的URL格式")

        # 验证URL是否为Telegram CDN
        if "cdn-telegram.org" not in decoded_url:
            raise HTTPException(status_code=403, detail="仅支持代理Telegram CDN的图片")

        # 确保session已初始化
        await http_client._ensure_session()

        # 获取图片内容
        async with http_client._session.get(
            url=decoded_url,
            timeout=aiohttp.ClientTimeout(total=30),
            ssl=False  # 禁用SSL验证
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="获取图片失败")
            
            # 读取二进制数据
            content = await response.read()
            
            # 获取正确的媒体类型
            content_type = response.headers.get("content-type", "image/jpeg")

        # 返回图片
        return Response(
            content=content,
            media_type=content_type,  # 使用实际的媒体类型
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理图片请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}") 