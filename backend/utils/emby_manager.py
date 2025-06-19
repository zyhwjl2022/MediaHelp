import os
from typing import Any, List, Dict, Optional, Union
from urllib.parse import urljoin
from loguru import logger
from utils.http_client import http_client
from utils.config_manager import config_manager

class EmbyManager:
    def __init__(self):
        """初始化 EmbyManager"""
        config = config_manager.get_config()
        self.base_url = config.get('emby_url')
        self.api_key = config.get('emby_api_key')
        
        if not self.base_url or not self.api_key:
            raise ValueError("Emby URL 和 API Key 必须在配置文件中提供")
        
        self.headers = {
            'X-Emby-Token': self.api_key,
            'Content-Type': 'application/json'
        }

    async def _make_request(self, endpoint: str, method: str = 'GET', params: dict = None, json: dict = None) -> dict:
        """发送请求到 Emby 服务器

        Args:
            endpoint (str): API 端点
            method (str, optional): HTTP 方法. Defaults to 'GET'.
            params (dict, optional): URL 参数. Defaults to None.
            json (dict, optional): JSON 请求体. Defaults to None.

        Returns:
            dict: 响应数据
        """
        url = urljoin(self.base_url, endpoint)
        response = await http_client.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=json
        )
        return response if isinstance(response, dict) else {}

    async def get_user_views(self, user_id: str) -> List[Dict]:
        """获取用户的媒体库视图

        Args:
            user_id (str): 用户ID

        Returns:
            List[Dict]: 媒体库视图列表
        """
        endpoint = f'/Users/{user_id}/Views'
        return await self._make_request(endpoint)

    async def get_items(self, user_id: str, parent_id: str = None, 
                     include_item_types: List[str] = None, 
                     recursive: bool = False,
                     sort_by: List[str] = None,
                     sort_order: str = None,
                     filters: List[str] = None,
                     limit: int = None,
                     fields: List[str] = None) -> Dict:
        """获取媒体项目列表

        Args:
            user_id (str): 用户ID
            parent_id (str, optional): 父文件夹ID. Defaults to None.
            include_item_types (List[str], optional): 包含的项目类型. Defaults to None.
            recursive (bool, optional): 是否递归获取. Defaults to False.
            sort_by (List[str], optional): 排序字段. Defaults to None.
            sort_order (str, optional): 排序方式 (Ascending/Descending). Defaults to None.
            filters (List[str], optional): 过滤条件. Defaults to None.
            limit (int, optional): 返回数量限制. Defaults to None.
            fields (List[str], optional): 返回字段. Defaults to None.

        Returns:
            Dict: 媒体项目列表
        """
        params = {
            'ParentId': parent_id,
            'Recursive': recursive,
            'IncludeItemTypes': ','.join(include_item_types) if include_item_types else None,
            'SortBy': ','.join(sort_by) if sort_by else None,
            'SortOrder': sort_order,
            'Filters': ','.join(filters) if filters else None,
            'Limit': limit,
            'Fields': ','.join(fields) if fields else None
        }
        
        # 移除 None 值的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        endpoint = f'/Users/{user_id}/Items'
        return await self._make_request(endpoint, params=params)

    async def get_item_details(self, user_id: str, item_id: str) -> Dict:
        """获取单个媒体项目的详细信息

        Args:
            user_id (str): 用户ID
            item_id (str): 项目ID

        Returns:
            Dict: 项目详细信息
        """
        endpoint = f'/Users/{user_id}/Items/{item_id}'
        return await self._make_request(endpoint)

    async def get_resumable_items(self, user_id: str, limit: int = 20) -> Dict:
        """获取可继续播放的项目

        Args:
            user_id (str): 用户ID
            limit (int, optional): 返回数量限制. Defaults to 20.

        Returns:
            Dict: 可继续播放的项目列表
        """
        return await self.get_items(
            user_id=user_id,
            recursive=True,
            filters=['IsResumable'],
            sort_by=['DatePlayed'],
            sort_order='Descending',
            limit=limit
        )

    async def get_all_movies(self, user_id: str) -> Dict:
        """获取所有电影

        Args:
            user_id (str): 用户ID

        Returns:
            Dict: 电影列表
        """
        return await self.get_items(
            user_id=user_id,
            recursive=True,
            include_item_types=['Movie']
        )

    async def get_all_episodes(self, user_id: str) -> Dict:
        """获取所有剧集

        Args:
            user_id (str): 用户ID

        Returns:
            Dict: 剧集列表
        """
        return await self.get_items(
            user_id=user_id,
            recursive=True,
            include_item_types=['Episode']
        )

    async def get_sync_jobs(self, target_id: str = None) -> Dict:
        """获取同步任务列表

        Args:
            target_id (str, optional): 目标设备ID. Defaults to None.

        Returns:
            Dict: 同步任务列表
        """
        params = {'TargetId': target_id} if target_id else None
        endpoint = '/Sync/Jobs'
        return await self._make_request(endpoint, params=params)

    async def create_sync_job(self, 
                          target_id: str,
                          item_ids: List[str],
                          quality: Optional[str] = None,
                          parent_id: Optional[str] = None,
                          unwatched_only: bool = False,
                          sync_new_content: bool = False,
                          item_limit: Optional[int] = None) -> Dict:
        """创建同步任务

        Args:
            target_id (str): 目标设备ID
            item_ids (List[str]): 要同步的项目ID列表
            quality (Optional[str], optional): 视频质量. Defaults to None.
            parent_id (Optional[str], optional): 父文件夹ID. Defaults to None.
            unwatched_only (bool, optional): 是否只同步未观看内容. Defaults to False.
            sync_new_content (bool, optional): 是否同步新内容. Defaults to False.
            item_limit (Optional[int], optional): 同步项目数量限制. Defaults to None.

        Returns:
            Dict: 创建的同步任务信息
        """
        data = {
            'TargetId': target_id,
            'ItemIds': item_ids,
            'Quality': quality,
            'ParentId': parent_id,
            'UnwatchedOnly': unwatched_only,
            'SyncNewContent': sync_new_content,
            'ItemLimit': item_limit
        }
        
        # 移除 None 值的参数
        data = {k: v for k, v in data.items() if v is not None}
        
        endpoint = '/Sync/Jobs'
        return await self._make_request(endpoint, method='POST', json=data)

    async def delete_sync_job(self, job_id: str) -> None:
        """删除同步任务

        Args:
            job_id (str): 同步任务ID
        """
        endpoint = f'/Sync/Jobs/{job_id}'
        await self._make_request(endpoint, method='DELETE')

    async def get_sync_job_status(self, job_id: str) -> Dict:
        """获取同步任务状态

        Args:
            job_id (str): 同步任务ID

        Returns:
            Dict: 同步任务状态信息
        """
        endpoint = f'/Sync/Jobs/{job_id}/Status'
        return await self._make_request(endpoint)

    async def get_sync_job_items(self, job_id: str) -> Dict:
        """获取同步任务中的项目列表

        Args:
            job_id (str): 同步任务ID

        Returns:
            Dict: 同步任务中的项目列表
        """
        endpoint = f'/Sync/Jobs/{job_id}/Items'
        return await self._make_request(endpoint)

    async def get_system_info(self) -> Dict:
        """获取 Emby 系统信息

        Returns:
            Dict: 系统信息
        """
        endpoint = '/System/Info'
        return await self._make_request(endpoint)

    async def search_items(self, search_term: str, include_item_types: List[str] = None, 
                         limit: int = 10, recursive: bool = True) -> Dict:
        """搜索媒体项目

        Args:
            search_term (str): 搜索关键词
            include_item_types (List[str], optional): 包含的项目类型. Defaults to None.
            limit (int, optional): 返回数量限制. Defaults to 10.
            recursive (bool, optional): 是否递归搜索. Defaults to True.

        Returns:
            Dict: 搜索结果
        """
        params = {
            'SearchTerm': search_term,
            'IncludeItemTypes': ','.join(include_item_types) if include_item_types else None,
            'Limit': str(limit),
            'Recursive': str(recursive).lower(),
            'ImageTypeLimit': '1'
        }
        
        # 移除 None 值的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        endpoint = '/Items'
        return await self._make_request(endpoint, params=params)

    async def refresh_item(self, item_id: str, recursive: bool = True, 
                         metadata_refresh_mode: str = "FullRefresh",
                         image_refresh_mode: str = "FullRefresh",
                         replace_all_metadata: bool = False,
                         replace_all_images: bool = False) -> bool:
        """刷新媒体项目元数据

        Args:
            item_id (str): 项目ID
            recursive (bool, optional): 是否递归刷新. Defaults to True.
            metadata_refresh_mode (str, optional): 元数据刷新模式. Defaults to "FullRefresh".
            image_refresh_mode (str, optional): 图片刷新模式. Defaults to "FullRefresh".
            replace_all_metadata (bool, optional): 是否替换所有元数据. Defaults to False.
            replace_all_images (bool, optional): 是否替换所有图片. Defaults to False.

        Returns:
            bool: 是否刷新成功
        """
        params = {
            'Recursive': str(recursive).lower(),
            'MetadataRefreshMode': metadata_refresh_mode,
            'ImageRefreshMode': image_refresh_mode,
            'ReplaceAllMetadata': str(replace_all_metadata).lower(),
            'ReplaceAllImages': str(replace_all_images).lower()
        }
        
        endpoint = f'/Items/{item_id}/Refresh'
        response = await self._make_request(endpoint, method='POST', params=params)
        return response == {}
    
    async def refresh_library(self) -> bool:
        """刷新整个媒体库

        Returns:
            bool: 是否刷新成功
        """
        try:
            endpoint = '/Library/Refresh'
            await self._make_request(endpoint, method='POST')
            return True
        except Exception as e:
            logger.error(f"刷新媒体库时出错: {str(e)}")
            return False
    
    async def searchAndRefreshItem(self, search_term: str) -> Any:
        """搜索媒体项目并刷新

        Args:
            search_term (str): 搜索关键词

        Returns:
            bool: 是否刷新成功
        """
        try:
            response = await self.search_items(search_term)            
            if not response.get('Items'):
                logger.warning(f"未找到匹配的项目: {search_term}")
                
            # 获取第一个匹配项的ID
            item_id = response['Items'][0]['Id']
            # 执行刷新
            if item_id:
                logger.info(f"找到匹配的项目: {item_id} 刷新")
                await self.refresh_item(item_id)
                return True
            else:
                logger.info("未找到匹配的项目,刷新整个媒体库")
                await self.refresh_library()
                return True
            
        except Exception as e:
            logger.error(f"搜索并刷新项目时出错: {str(e)}")
            return False

emby_manager = EmbyManager()
