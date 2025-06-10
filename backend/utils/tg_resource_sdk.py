import re
import aiohttp
import asyncio
from typing import Dict, List, Optional, TypedDict
from bs4 import BeautifulSoup
from loguru import logger
from utils.config_manager import config_manager

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
    _session: Optional[aiohttp.ClientSession] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TGResourceSDK, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化SDK"""
        self._headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

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

    async def _ensure_session(self):
        """确保会话已创建"""
        if self._session is None or self._session.closed:
            # 获取代理配置
            sys_config = config_manager.get_config()
            proxy = None
            if sys_config.get("use_proxy", False):
                proxy = f"http://{sys_config.get('proxy_host', '')}:{sys_config.get('proxy_port', '')}"
            
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                trust_env=True
            )
            if proxy:
                self._session._connector._ssl = False
                self._session._connector.proxy = proxy

    def _extract_cloud_links(self, text: str) -> tuple[List[str], str]:
        """提取云盘链接"""
        links: List[str] = []
        cloud_type = ""
        config = self._get_config()
        
        logger.info(f"开始提取云盘链接，配置: {config['cloudPatterns']}")  # 改用 info 级别
        
        for cloud_name, pattern in config["cloudPatterns"].items():
            logger.info(f"尝试匹配 {cloud_name} 云盘链接，使用模式: {pattern}")  # 改用 info 级别
            try:
                matches = re.findall(pattern, text)
                if matches:
                    logger.info(f"找到 {cloud_name} 云盘链接: {matches}")  # 改用 info 级别
                    links.extend(matches)
                    if not cloud_type:
                        cloud_type = cloud_name
            except Exception as e:
                logger.error(f"匹配 {cloud_name} 云盘链接时出错: {str(e)}")
                continue
        
        # 确保返回的链接是唯一的
        unique_links = list(set(links))
        logger.info(f"最终提取结果 - 链接: {unique_links}, 云盘类型: {cloud_type}")  # 改用 info 级别
        return unique_links, cloud_type

    async def _search_in_web(self, url: str) -> tuple[List[ResourceItem], str]:
        """在网页中搜索资源"""
        try:
            logger.info(f"[Task {id(asyncio.current_task())}] 开始执行搜索任务: {url}")
            await self._ensure_session()
            config = self._get_config()
            try:
                async with self._session.get(f"{config['telegram']['baseUrl']}{url}") as response:
                    logger.info(f"[Task {id(asyncio.current_task())}] 获取到响应: {url}, 状态码: {response.status}")
                    html = await response.text()
            except Exception as e:
                logger.error(f"[Task {id(asyncio.current_task())}] 请求失败: {url}", exc_info=e)
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
                    text_parts = text_element.get_text().split("\n", 1)
                    title = text_parts[0].strip()
                    content = text_parts[1].strip() if len(text_parts) > 1 else ""
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
                        logger.info(f"找到原始链接: {href}")  # 改用 info 级别，确保能看到日志
                    if text and text.startswith("#"):
                        tags.append(text)
                
                # 提取云盘链接
                all_links = " ".join(links)
                logger.info(f"准备提取云盘链接，原始链接文本: {all_links}")  # 改用 info 级别
                cloud_links, cloud_type = self._extract_cloud_links(all_links)
                logger.info(f"提取结果 - 云盘链接: {cloud_links}, 类型: {cloud_type}")  # 改用 info 级别
                
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
            logger.info(f"开始创建搜索任务，频道列表长度: {len(channel_list)}")
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
                logger.info(f"创建搜索任务: {url}")
                task = asyncio.create_task(self._search_in_web(url))
                task.set_name(f"search_{channel['id']}")
                tasks.append(task)
            
            logger.info(f"准备执行 {len(tasks)} 个搜索任务")
            # 等待所有搜索完成
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"任务 {tasks[i].get_name()} 执行失败: {str(result)}")
                    else:
                        logger.info(f"任务 {tasks[i].get_name()} 执行成功")
                
                # 过滤掉异常结果
                results = [r for r in results if not isinstance(r, Exception)]
                logger.info(f"所有搜索任务完成，成功获得 {len(results)} 个结果")
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
        finally:
            # 关闭会话
            if self._session and not self._session.closed:
                await self._session.close()

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