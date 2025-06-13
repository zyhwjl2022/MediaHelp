"""天翼云盘客户端"""

import random
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Any
from urllib.parse import urlparse, parse_qs, unquote
from urllib.parse import urlparse as parse_url
import asyncio

from loguru import logger
from utils.http_client import http_client
from utils.config_manager import ConfigManager

from .const import *
from .error import *
from .types import *
from .auth import CloudAuthClient
from .util import get_signature

class Cloud189Client:
    """天翼云盘客户端"""

    def __init__(self, username: str = "", password: str = "", cookies: str = "", sson_cookie: str = ""):
        """
        初始化客户端
        :param username: 用户名
        :param password: 密码
        :param cookies: cookies字符串
        :param sson_cookie: SSO Cookie
        """
        self.username = username
        self.password = password
        self.cookies = cookies
        self.sson_cookie = sson_cookie
        self.auth_client = CloudAuthClient()
        self.session: Optional[ClientSession] = None
        self.user_info: Optional[UserInfo] = None
        self.config_manager = ConfigManager()

    def _load_session_from_config(self) -> bool:
        """从配置文件加载session"""
        config = self.config_manager.get_config()
        cloud189_session = config.get("cloud189_session")
        
        if cloud189_session:
            # 检查session是否过期
            expires_in = cloud189_session.get("expires_in", 0)
            if expires_in > time.time():
                self.session = cloud189_session
                return True
        return False

    def _save_session_to_config(self):
        """保存session到配置文件"""
        if self.session:
            self.config_manager.update_config({
                "cloud189_session": self.session
            })

    async def _send_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        :param method: 请求方法
        :param url: 请求地址
        :param kwargs: 其他参数
        :return: 响应数据
        :raises: NetworkError 当请求失败时
        """
        headers = DEFAULT_HEADERS.copy()
        
        # 添加基础headers
        if self.cookies:
            headers["Cookie"] = self.cookies
            
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]

        # 处理参数中的布尔值
        if "params" in kwargs:
            kwargs["params"] = {k: str(v).lower() if isinstance(v, bool) else v 
                              for k, v in kwargs["params"].items()}

        # 添加sessionKey
        if "params" in kwargs:
            kwargs["params"]["sessionKey"] = self.session["session_key"]
        else:
            kwargs["params"] = {"sessionKey": self.session["session_key"]}
            
        # 添加noCache
        if "params" in kwargs:
            kwargs["params"]["noCache"] = str(random.random())
        else:
            kwargs["params"] = {"noCache": str(random.random())}
            
        # 添加认证信息
        if self.session:
            # API URL处理
            if API_URL in url:
                time_stamp = str(int(time.time() * 1000))
                params = kwargs.get("params", {})
                if method.upper() == "GET":
                    sign_data = {
                        **params,
                        "Timestamp": time_stamp,
                        "AccessToken": self.session["access_token"]
                    }
                else:
                    sign_data = {
                        **(kwargs.get("data", {}) or kwargs.get("json", {})),
                        "Timestamp": time_stamp,
                        "AccessToken": self.session["access_token"]
                    }
                
                signature = get_signature(sign_data)
                
                headers.update({
                    "Sign-Type": "1",
                    "Signature": signature,
                    "Timestamp": time_stamp,
                    "Accesstoken": self.session["access_token"]
                })
                
            # WEB URL处理
            elif WEB_URL in url:
                parsed_url = parse_url(url)
                # headers.update({
                #     "'Accept': 'application/json;charset=UTF-8'"
                # })
                if "/open" in parsed_url.path:
                    time_stamp = str(int(time.time() * 1000))
                    app_key = "600100422"
                    
                    if method.upper() == "GET":
                        params = kwargs.get("params", {})
                        sign_data = {
                            **params,
                            "Timestamp": time_stamp,
                            "AppKey": app_key
                        }
                    else:
                        sign_data = {
                            **(kwargs.get("data", {}) or kwargs.get("json", {})),
                            "Timestamp": time_stamp,
                            "AppKey": app_key
                        }
                    
                    signature = get_signature(sign_data)
                    headers.update({
                        "Sign-Type": "1",
                        "Signature": signature,
                        "Timestamp": time_stamp,
                        "AppKey": app_key,
                        "Accept": "application/json;charset=UTF-8"
                    })

        try:
            response = await http_client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
                        
            if isinstance(response, str):
                data = json.loads(response)
                
                # 处理token失效
                if isinstance(data, dict):
                    error_code = data.get("errorCode")
                    if error_code == "InvalidAccessToken":
                        logger.debug("AccessToken已失效,正在刷新...")
                        await self.login()
                        return await self._send_request(method, url, **kwargs)
                    elif error_code == "InvalidSessionKey":
                        logger.debug("SessionKey已失效,正在刷新...")
                        await self.login()
                        return await self._send_request(method, url, **kwargs)
                        
                check_error(data)
                return data
                
            return response
            
        except Exception as e:
            logger.error(f"请求失败: {str(e)}")
            raise NetworkError(f"请求失败: {str(e)}")

    async def login(self) -> bool:
        """
        登录并初始化客户端
        :return: 是否登录成功
        """
        try:
            # 首先尝试从配置文件加载session
            if self._load_session_from_config():
                logger.info("从配置文件加载session成功")
                # 验证session是否有效
                if await self.init():
                    return True
                logger.info("配置文件中的session已失效，尝试重新登录")
            
            session = None
            
            logger.info(f"尝试登录: {self.username} {self.password} {self.sson_cookie}")
            # 尝试不同的登录方式
            if self.username and self.password:
                session = await self.auth_client.login_by_password(
                    self.username,
                    self.password
                )
            elif self.sson_cookie:
                session = await self.auth_client.login_by_sson_cookie(
                    self.sson_cookie
                )
            
            logger.info(f"登录结果: {session}")
            if not session:
                return False
                
            self.session = {
                "access_token": session["accesstoken"],
                "session_key": session["sessionkey"],
                "expires_in": int(time.time() + 6 * 24 * 60 * 60)
            }
            
            # 保存session到配置文件
            self._save_session_to_config()
            
            # 获取用户信息
            return await self.init()
            
        except Exception as e:
            logger.error(f"登录失败：{str(e)}")
            return False

    async def init(self) -> bool:
        """
        初始化客户端
        :return: 是否初始化成功
        """
        try:
            info = await self.get_user_info()
            if info:
                self.user_info = {
                    "account": info.get("account", ""),
                    "cloud_capacity_info": info.get("cloudCapacityInfo", {}),
                    "family_capacity_info": info.get("familyCapacityInfo", {})
                }
                return True
            return False
        except Exception as e:
            logger.error(f"初始化失败：{str(e)}")
            return False

    async def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        return await self._send_request(
            "GET",
            f"{WEB_URL}/api/portal/getUserSizeInfo.action"
        )
    
    async def get_share_info(self, share_code: str) -> ShareInfo:
        """
        获取分享信息
        :param share_code: 分享码
        """
        result = await self._send_request(
            "GET",
            f"{WEB_URL}/api/open/share/getShareInfoByCodeV2.action",
            params={"shareCode": share_code}
        )
        logger.info(f"获取分享信息: {result}")
        return result

    async def list_share_files(
        self,
        share_id: str,
        file_id: str = ROOT_FOLDER_ID,
        share_mode: str = "1",
        access_code: str = "",
        is_folder: bool = True
    ) -> List[FileInfo]:
        """
        获取分享文件列表
        :param share_id: 分享ID
        :param file_id: 文件ID
        :param share_mode: 分享模式
        :param access_code: 访问码
        """
        result = await self._send_request(
            "GET",
            f"{WEB_URL}/api/open/share/listShareDir.action",
            params={
                "shareId": share_id,
                "fileId": file_id,
                "isFolder": is_folder,
                "orderBy": "lastOpTime",
                "descending": True,
                "shareMode": share_mode,
                "pageNum": 1,
                "pageSize": 1000,
                "accessCode": access_code
            }
        )
        
        return result

    async def list_files(self, folder_id: str = ROOT_FOLDER_ID) -> FileListResponse:
        """
        获取文件列表
        :param folder_id: 文件夹ID
        """
        result = await self._send_request(
            "GET",
            f"{WEB_URL}/api/open/file/listFiles.action",
            params={
                "folderId": folder_id,
                "mediaType": 0,
                "orderBy": "lastOpTime",
                "descending": True,
                "pageNum": 1,
                "pageSize": 1000
            }
        )
        return result

    async def create_batch_task(self, task_params: BatchTaskParams) -> TaskResponse:
        """
        创建批量任务
        :param task_params: 任务参数
        """        
        # 构建表单数据
        form_data = {
            "type": task_params["type"],
            "taskInfos": json.dumps(task_params["taskInfos"], ensure_ascii=False),  # 将taskInfos转为JSON字符串
            "targetFolderId": task_params["targetFolderId"],
            "shareId": task_params["shareId"]
        }    
        logger.info(f"创建批量任务参数: {form_data}")
            
        result = await self._send_request(
            "POST",
            f"{WEB_URL}/api/open/batch/createBatchTask.action",
            data=form_data,  # 使用data参数，http client会自动进行URL编码
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return result

    async def check_task_status(self, task_id: str, task_type: str = TASK_TYPE_SHARE_SAVE) -> TaskResponse:
        """
        检查任务状态
        :param task_id: 任务ID
        :param task_type: 任务类型
        """
        result = await self._send_request(
            "POST",
            f"{WEB_URL}/api/open/batch/checkBatchTask.action",
            data={"taskId": task_id, "type": task_type},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return result

    async def get_conflict_task_info(self, task_id: str) -> Dict[str, Any]:
        """
        获取冲突任务信息
        :param task_id: 任务ID
        :return: 冲突任务信息
        """
        result = await self._send_request(
            "POST",
            f"{WEB_URL}/api/open/batch/getConflictTaskInfo.action",
            json={
                "taskId": task_id,
                "type": TASK_TYPE_SHARE_SAVE
            }
        )
        return result

    async def manage_batch_task(
        self, 
        task_id: str,
        target_folder_id: str,
        task_infos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        处理批量任务中的文件冲突
        :param task_id: 任务ID
        :param target_folder_id: 目标文件夹ID
        :param task_infos: 任务信息列表，格式为：
                         [{"fileId":"","fileName":"","isConflict":1,"isFolder":0,"dealWay":1}]
                         dealWay: 1-跳过, 2-覆盖, 3-保存副本
        :return: 处理结果
        """
        result = await self._send_request(
            "POST",
            f"{WEB_URL}/api/open/batch/manageBatchTask.action",
            json={
                "taskId": task_id,
                "type": TASK_TYPE_SHARE_SAVE,
                "targetFolderId": target_folder_id,
                "taskInfos": task_infos
            }
        )
        return result

    async def search_files(self, filename: str) -> FileListResponse:
        """
        搜索文件
        :param filename: 文件名关键词
        """
        result = await self._send_request(
            "GET",
            f"{API_URL}/open/file/searchFiles.action",
            params={
                "folderId": ROOT_FOLDER_ID,
                "pageSize": "1000",
                "pageNum": "1",
                "recursive": 1,
                "mediaType": 0,
                "filename": filename
            }
        )
        return result

    async def get_download_url(self, file_id: str, share_id: str = None) -> str:
        """
        获取下载链接
        :param file_id: 文件ID
        :param share_id: 分享ID（可选）
        """
        file_type = 4 if share_id else 2
        response = await self._send_request(
            "GET",
            f"{API_URL}/portal/getNewVlcVideoPlayUrl.action",
            params={
                "fileId": file_id,
                "shareId": share_id,
                "type": file_type,
                "dt": 1
            }
        )

        normal = response.get("normal", {})
        url = normal.get("url")
        
        async with http_client._session.get(
            url,
            follow_redirects=False,
            headers=DEFAULT_HEADERS
        ) as res:
            return res.headers.get("location", "")

    async def create_folder(self, folder_name: str, parent_id: str = ROOT_FOLDER_ID) -> Dict[str, Any]:
        """
        创建文件夹
        :param folder_name: 文件夹名称
        :param parent_id: 父文件夹ID
        """
        result = await self._send_request(
            "POST",
            f"{API_URL}/open/file/createFolder.action",
            data={
                "parentFolderId": parent_id,
                "folderName": folder_name
            }
        )
        return result

    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """
        重命名文件
        :param file_id: 文件ID
        :param new_name: 新名称
        """
        result = await self._send_request(
            "POST",
            f"{API_URL}/open/file/renameFile.action",
            data={
                "fileId": file_id,
                "destFileName": new_name
            }
        )
        return result

    async def check_access_code(self, share_code: str, access_code: str) -> Dict[str, Any]:
        """
        验证访问码
        :param share_code: 分享码
        :param access_code: 访问码
        """
        result = await self._send_request(
            "GET",
            f"{API_URL}/open/share/checkAccessCode.action",
            params={
                "shareCode": share_code,
                "accessCode": access_code
            }
        )
        return result

    @staticmethod
    def parse_share_code(share_link: str) -> str:
        """
        解析分享链接，提取分享码
        :param share_link: 分享链接
        :return: 分享码
        :raises: ValueError 当无法解析分享码时抛出异常
        """
        try:
            if isinstance(share_link, tuple):
                share_link = share_link[0]  # 如果是元组，取第一个元素
                
            share_url = urlparse(share_link)
            share_code = None
            
            if "content.21cn.com" in share_url.netloc:
                # 处理订阅链接
                if share_url.fragment:
                    query = share_url.fragment.split('?', 1)[1]
                    params = parse_qs(query)
                    share_code = params.get('shareCode', [None])[0]
            elif share_url.path == '/web/share':
                # 处理 web/share 格式
                params = parse_qs(share_url.query)
                share_code = params.get('code', [None])[0]
            elif share_url.path.startswith('/t/'):
                # 处理 /t/xxx 格式
                share_code = share_url.path.split('/')[-1]
            elif share_url.fragment and '/t/' in share_url.fragment:
                # 处理带 hash 的格式
                share_code = share_url.fragment.split('/')[-1]
            elif 'share.html' in share_url.path:
                # 处理 share.html 格式
                if share_url.fragment:
                    share_code = share_url.fragment.split('/')[-1]
            
            if not share_code:
                raise ValueError('无效的分享链接')
                
            return share_code
            
        except Exception as e:
            raise ValueError(f'解析分享链接失败: {str(e)}')

    @staticmethod
    def parse_cloud_share(share_text: str) -> Tuple[str, str]:
        """
        解析分享文本，提取链接和访问码
        :param share_text: 分享文本
        :return: (url, access_code) 元组
        """
        # 移除所有空格并解码
        share_text = unquote(share_text.replace(' ', ''))
        
        # 访问码匹配模式
        access_code_patterns = [
            r'[（(]访问码[：:]\s*([a-zA-Z0-9]{4})[)）]',  # （访问码：xxxx）
            r'[（(]提取码[：:]\s*([a-zA-Z0-9]{4})[)）]',  # （提取码：xxxx）
            r'访问码[：:]\s*([a-zA-Z0-9]{4})',           # 访问码：xxxx
            r'提取码[：:]\s*([a-zA-Z0-9]{4})',           # 提取码：xxxx
            r'[（(]([a-zA-Z0-9]{4})[)）]'                # （xxxx）
        ]
        
        # URL匹配模式
        url_patterns = [
            r'(https?://cloud\.189\.cn/web/share\?[^\s]+)',     # web/share格式
            r'(https?://cloud\.189\.cn/t/[a-zA-Z0-9]+)',        # t/xxx格式
            r'(https?://h5\.cloud\.189\.cn/share\.html#/t/[a-zA-Z0-9]+)', # h5分享格式
            r'(https?://[^/]+/web/share\?[^\s]+)',              # 其他域名的web/share格式
            r'(https?://[^/]+/t/[a-zA-Z0-9]+)',                 # 其他域名的t/xxx格式
            r'(https?://[^/]+/share\.html[^\s]*)',               # share.html格式
            r'(https?://content\.21cn\.com[^\s]+)'                # 订阅链接格式
        ]
        
        # 提取访问码
        access_code = ''
        for pattern in access_code_patterns:
            match = re.search(pattern, share_text)
            if match:
                access_code = match.group(1)
                # 从原文本中移除访问码部分
                share_text = share_text.replace(match.group(0), '')
                break
        
        # 提取URL
        url = ''
        for pattern in url_patterns:
            match = re.search(pattern, share_text)
            if match:
                url = match.group(1)
                break
        
        return url, access_code

    async def save_share_files(
        self,
        share_url: str,
        target_folder_id: str = ROOT_FOLDER_ID,
        file_ids: Optional[List[BatchTaskInfo]] = None
    ) -> SaveShareResult:
        """
        保存分享文件
        :param share_url: 分享链接
        :param target_folder_id: 目标文件夹ID
        :param file_ids: 要保存的文件信息列表
        :return: 保存结果
        """
        try:
            # 解析分享链接
            logger.info(f"解析分享链接: {share_url}")
            url, _ = self.parse_cloud_share(share_url)
            if not url:
                raise Cloud189Error("无效的分享链接")
                
            # 获取分享码
            share_code = self.parse_share_code(url)
            
            # 获取分享信息
            share_info = await self.get_share_info(share_code)
            
            logger.info(f"分享信息: {file_ids}")
            # 创建批量保存任务
            task_infos = []
            for file in (file_ids or []):
                task_info = {
                    "fileId": file["fileId"] if isinstance(file, dict) else file.fileId,
                }
                # 处理文件名
                if isinstance(file, dict) and "fileName" in file:
                    task_info["fileName"] = file["fileName"]
                elif hasattr(file, "fileName"):
                    task_info["fileName"] = file.fileName
                    
                # 处理是否为文件夹，转换为数字
                is_folder = False
                if isinstance(file, dict) and "isFolder" in file:
                    is_folder = file["isFolder"]
                elif hasattr(file, "isFolder"):
                    is_folder = file.isFolder
                task_info["isFolder"] = 1 if is_folder else 0
                
                task_infos.append(task_info)
            
            task_params: ShareSaveTaskParams = {
                "type": TASK_TYPE_SHARE_SAVE,
                "taskInfos": task_infos,
                "targetFolderId": target_folder_id,
                "shareId": share_info["shareId"]
            }
            
            logger.info(f"任务参数: {task_params}")
            
            # 创建任务
            task = await self.create_batch_task(task_params)
            
            # 检查任务状态
            start_time = time.time()
            status = await self.check_task_status(task["taskId"])
            while status["taskStatus"] in [1, 3]:  # 1和3表示任务进行中
                # 检查是否超时(1分钟)
                if time.time() - start_time > 5:
                    logger.error(f"任务 {task['taskId']} 执行超时")
                    return {
                        "message": "文件保存失败：任务执行超时(超过5秒)",
                        "task_id": task["taskId"],
                        "status": status
                    }
                await asyncio.sleep(.5)  # 暂停2秒
                status = await self.check_task_status(task["taskId"])
                
            if status["taskStatus"] == 2:  # 2表示有文件冲突
                # 获取冲突任务信息
                conflict_task_info = await self.get_conflict_task_info(task["taskId"])
                if not conflict_task_info:
                    raise Cloud189Error("获取冲突任务信息失败")
                    
                # 设置所有冲突文件的处理方式为忽略冲突(dealWay=1)
                for task_info in conflict_task_info["taskInfos"]:
                    task_info["dealWay"] = 1
                    
                # 处理冲突
                await self.manage_batch_task(
                    task["taskId"], 
                    conflict_task_info["targetFolderId"], 
                    conflict_task_info["taskInfos"]
                )
                
                # 等待200ms
                await asyncio.sleep(.5)
                
                # 继续检查任务状态
                start_time = time.time()  # 重置开始时间
                status = await self.check_task_status(task["taskId"])
                while status["taskStatus"] in [1, 3]:  # 继续等待任务完成
                    # 检查是否超时(1分钟)
                    if time.time() - start_time > 5:
                        logger.error(f"任务 {task['taskId']} 执行超时")
                        return {
                            "message": "文件保存失败：任务执行超时(超过5秒)",
                            "task_id": task["taskId"],
                            "status": status
                        }
                    await asyncio.sleep(0.5)
                    status = await self.check_task_status(task["taskId"])
                    
            if status["taskStatus"] == 4:  # 4表示任务成功完成
                # 检查是否有失败的文件
                if status.get("failedCount", 0) > 0:
                    # 获取目标文件夹中的所有文件
                    folder_files = await self.list_files(target_folder_id)
                    
                    # 获取原始任务信息中的文件列表
                    task_files = task_params["taskInfos"]
                    
                    # 找出未成功保存的文件（可能是被和谐的文件）
                    failed_files = []
                    for task_file in task_files:
                        file_exists = any(
                            folder_file.get("md5") == task_file.get("md5")
                            for folder_file in folder_files
                        )
                        if not file_exists:
                            failed_files.append(task_file)
                    
                    # 记录失败的文件信息
                    if failed_files:
                        logger.warning(
                            f"任务 {task['taskId']} 完成，但有 {len(failed_files)} 个文件未成功保存，"
                            f"可能被和谐: {[f.get('fileName', '') for f in failed_files]}"
                        )
                        
                    return {
                        "message": "文件保存完成",
                        "task_id": task["taskId"],
                        "status": status,
                        "failed_files": failed_files,
                        "failed_count": len(failed_files)
                    }
                
                # 全部成功的情况
                success_message = "文件保存成功"
                if status.get("dealCount", 0) > 0:  # 如果有处理过冲突
                    success_message += "(已自动处理文件冲突)"
                    
                return {
                    "message": success_message,
                    "task_id": task["taskId"],
                    "status": status
                }
            else:
                # 其他状态都视为失败
                raise Cloud189Error(f"文件保存失败: 任务状态异常 {status['taskStatus']}")
                
        except Exception as e:
            logger.error(f"保存分享文件失败：{str(e)}")
            raise Cloud189Error(f"保存分享文件失败：{str(e)}")