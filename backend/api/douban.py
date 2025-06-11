from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import urllib3
from datetime import datetime, timedelta
from loguru import logger
from utils.http_client import http_client

from api.deps import get_current_user
from models.user import User
from schemas.response import Response

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter(prefix="/douban", tags=["豆瓣"])


class DoubanSubject(BaseModel):
    id: str
    title: str
    rate: Optional[str]
    cover: str
    url: str
    cover_x: Optional[int]
    cover_y: Optional[int]
    is_new: Optional[bool] = False
    episodes_info: Optional[str] = ""
    playable: Optional[bool] = False
    type: Optional[str] = None
    card_subtitle: Optional[str] = None
    description: Optional[str] = None
    honor_infos: Optional[List[str]] = None
    year: Optional[str] = None
    release_date: Optional[str] = None
    directors: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    regions: Optional[List[str]] = None


class Cache:
    def __init__(self, expire_minutes: int = 30):
        self.cache: Dict[str, tuple] = {}
        self.expire_minutes = expire_minutes

    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=self.expire_minutes):
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: any):
        self.cache[key] = (value, datetime.now())


class DoubanService:
    def __init__(self):
        self.base_url = "https://m.douban.com/rexxar/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://movie.douban.com",
            "Referer": "https://movie.douban.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=1, i"
        }
        self.cache = Cache(expire_minutes=30)

    async def _get_with_retry(self, url: str, params: dict = None, max_retries: int = 3) -> Dict:
        """带重试的GET请求"""
        cache_key = f"{url}_{str(params)}"
        cached_response = self.cache.get(cache_key)
        if cached_response:
            return cached_response

        try:
            response = await http_client.get(
                url,
                params=params,
                headers=self.headers,
                retry_times=max_retries
            )
            if isinstance(response, str):
                return {}
            self.cache.set(cache_key, response)
            return response
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise HTTPException(status_code=503, detail="豆瓣API访问失败")

    def _get_cover_url(self, item: dict) -> str:
        """获取封面图片URL"""
        # 优先使用高清图片
        if "pic" in item and item["pic"].get("normal"):
            return item["pic"]["normal"]
        # 备选使用封面图片
        if "cover" in item and item["cover"].get("url"):
            return item["cover"]["url"]
        return ""

    def _convert_to_subject(self, item: dict) -> DoubanSubject:
        """将API返回的数据转换为DoubanSubject对象"""
        return DoubanSubject(
            id=str(item.get("id")),
            title=item.get("title", ""),
            rate=str(item.get("rating", {}).get("value", "")),
            cover=self._get_cover_url(item),
            url=f"https://movie.douban.com/subject/{item.get('id')}/",
            cover_x=item.get("cover", {}).get("width"),
            cover_y=item.get("cover", {}).get("height"),
            is_new=item.get("is_new", False),
            type=item.get("type"),
            card_subtitle=item.get("card_subtitle"),
            description=item.get("description"),
            honor_infos=item.get("honor_infos"),
            year=item.get("year"),
            release_date=item.get("release_date"),
            directors=[p.get("name") for p in item.get("directors", []) if p.get("name")],
            actors=[p.get("name") for p in item.get("actors", []) if p.get("name")],
            regions=item.get("regions", [])
        )

    async def get_hot_list(
        self,
        type: str = "movie",
        category: str = None,
        page: int = 1,
        count: int = 20
    ) -> List[DoubanSubject]:
        """获取热门电影、电视剧或综艺列表"""
        try:
            start = (page - 1) * count
            url = f"{self.base_url}/subject/recent_hot/{type}"
            params = {
                "start": start,
                "limit": count
            }
            
            if type == "tv":
                params.update({"type": "tv"})
                if category == "show":
                    # 综艺节目
                    params.update({
                        "category": "show",
                        "type": "show"
                    })
            
            response = await self._get_with_retry(url, params)
            
            if "items" in response:
                return [self._convert_to_subject(item) for item in response["items"]]
            return []

        except Exception as e:
            logger.error(f"获取豆瓣热门列表失败: {e}")
            raise HTTPException(status_code=500, detail="获取豆瓣热门列表失败")


douban_service = DoubanService()


@router.get("/hot_list", response_model=Response[List[DoubanSubject]])
async def get_douban_hot_list(
    type: str = Query(default="movie", description="类型：movie(电影)、tv(电视剧)"),
    category: str = Query(default=None, description="分类：show(综艺)，仅在type=tv时有效"),
    page: int = Query(default=1, description="页码"),
    count: int = Query(default=50, description="每页数量"),
    current_user: User = Depends(get_current_user)
) -> Response[List[DoubanSubject]]:
    data = await douban_service.get_hot_list(
        type=type,
        category=category,
        page=page,
        count=count
    )
    return Response(data=data)
