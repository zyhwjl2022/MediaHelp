import asyncio
import re
from typing import Dict, List, Optional, TypedDict
from bs4 import BeautifulSoup
from loguru import logger
from utils.config_manager import config_manager
from utils.http_client import http_client

class ChannelInfo(TypedDict):
    """频道信息"""
    id: str
    name: str
    channelLogo: str

class ResourceItem(TypedDict):
    """资源项"""
    messageId: Optional[str]
    title: Optional[str]
    completeTitle: Optional[str]
    link: Optional[str]
    pubDate: Optional[str]
    content: Optional[str]
    description: Optional[str]
    image: Optional[str]
    cloudLinks: List[str]
    tags: List[str]
    cloudType: Optional[str]
    channel: Optional[str]
    channelId: Optional[str]

class SearchResult(TypedDict):
    """搜索结果"""
    list: List[ResourceItem]
    channelInfo: ChannelInfo
    id: str

class TGResourceSDK:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TGResourceSDK, cls).__new__(cls)
        return cls._instance

    def _get_config(self) -> dict:
        """获取配置"""
        config = config_manager.get_config()
        return config.get("tg_resource", {
            "telegram": {
                "baseUrl": "https://t.me/s",
                "channels": []
            },
            "cloudPatterns": {}
        })

    def _extract_cloud_links(self, text: str) -> tuple[List[str], str]:
        """提取云盘链接"""
        links: List[str] = []
        cloud_type = ""
        config = self._get_config()
        
        for cloud_name, pattern in config["cloudPatterns"].items():
            try:
                matches = re.findall(pattern, text)
                if matches:
                    links.extend(matches)
                    if not cloud_type:
                        cloud_type = cloud_name
            except Exception as e:
                logger.error(f"匹配 {cloud_name} 云盘链接时出错: {str(e)}")
                continue
        
        unique_links = list(set(links))
        return unique_links, cloud_type

    async def _search_in_web(self, url: str) -> tuple[List[ResourceItem], str]:
        """在网页中搜索资源"""
        try:
            config = self._get_config()
            
            try:
                html = await http_client.get(f"{config['telegram']['baseUrl']}{url}")
            except Exception as e:
                logger.error(f"请求失败: {url}", exc_info=e)
                raise
            
            soup = BeautifulSoup(html, 'html.parser')
            items: List[ResourceItem] = []
            channel_logo = ""
            
            # 获取频道logo
            header_link = soup.select_one(".tgme_header_link")
            if header_link:
                logo_img = header_link.find("img")
                if logo_img:
                    channel_logo = logo_img.get("src", "")
            
            # 遍历消息
            for message in soup.select(".tgme_widget_message_wrap"):
                # 获取消息ID
                message_element = message.select_one(".tgme_widget_message")
                message_id = message_element.get("data-post", "").split("/")[1] if message_element else None
                
                # 获取消息文本
                text_element = message.select_one(".js-message_text")
                if text_element:
                    # 获取原始HTML内容
                    html_content = str(text_element)
                    
                    # 提取标题 (第一个<br>标签前的内容)
                    title_match = re.split("<br.*?>", html_content, 1)
                    title = BeautifulSoup(title_match[0], 'html.parser').get_text().strip()
                    
                    # 提取描述 (第一个<a>标签前面的内容，不包含标题)
                    content_html = html_content.replace(title_match[0], "", 1)
                    content_parts = re.split("<a.*?>", content_html, 1)
                    content = BeautifulSoup(content_parts[0], 'html.parser').get_text().replace("<br>", "").strip()
                else:
                    title = ""
                    content = ""
                
                # 获取发布时间
                time_element = message.select_one("time")
                pub_date = time_element.get("datetime") if time_element else None
                
                # 获取图片
                photo_wrap = message.select_one(".tgme_widget_message_photo_wrap")
                image = None
                if photo_wrap:
                    style = photo_wrap.get("style", "")
                    image_match = re.search(r"url\('(.+?)'\)", style)
                    image = image_match.group(1) if image_match else None
                
                # 获取标签和链接
                tags: List[str] = []
                links: List[str] = []
                for a in message.select(".tgme_widget_message_text a"):
                    href = a.get("href")
                    text = a.get_text()
                    if href:
                        links.append(href)
                    if text and text.startswith("#"):
                        tags.append(text)
                
                # 提取云盘链接
                all_links = " ".join(links)
                cloud_links, cloud_type = self._extract_cloud_links(all_links)
                
                # 创建资源项
                item: ResourceItem = {
                    "messageId": message_id,
                    "title": title,
                    "completeTitle": None,
                    "link": None,
                    "pubDate": pub_date,
                    "content": content,
                    "description": None,
                    "image": image,
                    "cloudLinks": cloud_links,
                    "tags": tags,
                    "cloudType": cloud_type,
                    "channel": None,
                    "channelId": None
                }
                
                items.append(item)
            
            return items, channel_logo
            
        except Exception as e:
            logger.error(f"搜索错误: {url}", exc_info=e)
            return [], ""

    async def search_all(self, keyword: str = "", channel_id: str = None, message_id: str = None) -> Dict[str, List[SearchResult]]:
        """搜索所有资源"""
        try:
            all_results: List[SearchResult] = []
            config = self._get_config()
            
            # 过滤频道列表
            channel_list = (
                [c for c in config["telegram"]["channels"] if c["id"] == channel_id]
                if channel_id
                else config["telegram"]["channels"]
            )
            
            # 并行搜索所有频道
            tasks = []
            for channel in channel_list:
                message_id_params = f"before={message_id}" if message_id else ""
                url = f"/{channel['id']}"
                if keyword or message_id:
                    url += "?"
                    if keyword:
                        url += f"q={keyword}"
                        if message_id:
                            url += "&"
                    if message_id:
                        url += message_id_params
                tasks.append(self._search_in_web(url))
            
            # 等待所有搜索完成 
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"任务 {i} 执行失败: {str(result)}")
                
                # 过滤掉异常结果
                results = [r for r in results if not isinstance(r, Exception)]
            except Exception as e:
                logger.error("执行任务时发生错误", exc_info=e)
                raise
            
            # 处理结果
            for (items, channel_logo), channel in zip(results, channel_list):
                if items:
                    channel_results = []
                    for item in items:
                        if item["cloudLinks"]:
                            item["channel"] = channel["name"]
                            item["channelId"] = channel["id"]
                            channel_results.append(item)
                    
                    if channel_results:
                        all_results.append({
                            "list": channel_results,
                            "channelInfo": {
                                **channel,
                                "channelLogo": channel_logo
                            },
                            "id": channel["id"]
                        })
            
            return {"data": all_results}
            
        except Exception as e:
            logger.error("搜索失败", exc_info=e)
            return {"data": []}

    async def update_config(self, channels: List[Dict[str, str]] = None, patterns: Dict[str, str] = None):
        """更新SDK配置"""
        config = self._get_config()
        
        if channels is not None:
            config["telegram"]["channels"] = channels
        if patterns is not None:
            config["cloudPatterns"] = patterns
            
        config_manager.update_config({"tg_resource": config})

# 创建全局实例
tg_resource = TGResourceSDK() 