import re
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from urllib.parse import quote_plus
from loguru import logger
from utils.http_client import http_client

class QuarkSDK:
    """夸克网盘 SDK"""
    
    BASE_URL = "https://drive-pc.quark.cn"
    BASE_URL_APP = "https://drive-m.quark.cn"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) quark-cloud-drive/3.14.2 Chrome/112.0.5615.165 Electron/24.1.3.8 Safari/537.36 Channel/pckk_other_ch"

    def __init__(self, cookie: str = ""):
        """
        初始化夸克网盘 SDK
        :param cookie: 夸克网盘 cookie
        """
        self.cookie = cookie.strip()
        self.is_active = False
        self.nickname = ""
        self.mparam = self._match_mparam_from_cookie(cookie)

    def _match_mparam_from_cookie(self, cookie: str) -> Dict[str, str]:
        """从 cookie 中提取 mparam 参数"""
        mparam = {}
        kps_match = re.search(r"(?<!\w)kps=([a-zA-Z0-9%+/=]+)[;&]?", cookie)
        sign_match = re.search(r"(?<!\w)sign=([a-zA-Z0-9%+/=]+)[;&]?", cookie)
        vcode_match = re.search(r"(?<!\w)vcode=([a-zA-Z0-9%+/=]+)[;&]?", cookie)
        
        if kps_match and sign_match and vcode_match:
            mparam = {
                "kps": kps_match.group(1).replace("%25", "%"),
                "sign": sign_match.group(1).replace("%25", "%"),
                "vcode": vcode_match.group(1).replace("%25", "%"),
            }
        return mparam

    async def _send_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        headers = {
            "cookie": self.cookie,
            "content-type": "application/json",
            "user-agent": self.USER_AGENT,
        }
        
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
            
        # 处理分享链接的特殊请求
        if self.mparam and "share" in url and self.BASE_URL in url:
            url = url.replace(self.BASE_URL, self.BASE_URL_APP)
            kwargs["params"] = kwargs.get("params", {})
            kwargs["params"].update({
                "device_model": "M2011K2C",
                "entry": "default_clouddrive",
                "_t_group": "0%3A_s_vp%3A1",
                "dmn": "Mi%2B11",
                "fr": "android",
                "pf": "3300",
                "bi": "35937",
                "ve": "7.4.5.680",
                "ss": "411x875",
                "mi": "M2011K2C",
                "nt": "5",
                "nw": "0",
                "kt": "4",
                "pr": "ucpro",
                "sv": "release",
                "dt": "phone",
                "data_from": "ucapi",
                "kps": self.mparam.get("kps"),
                "sign": self.mparam.get("sign"),
                "vcode": self.mparam.get("vcode"),
                "app": "clouddrive",
                "kkkk": "1",
            })
            del headers["cookie"]

        try:
            response = await http_client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            if isinstance(response, str):
                return json.loads(response)
            return response
        except Exception as e:
            logger.error(f"请求异常：{str(e)}")
            return {
                "status": 500,
                "code": 1,
                "message": f"请求异常：{str(e)}"
            }

    async def init(self) -> Union[Dict[str, Any], bool]:
        """初始化账号信息"""
        account_info = await self.get_account_info()
        if account_info:
            self.is_active = True
            self.nickname = account_info["nickname"]
            return account_info
        return False

    async def get_account_info(self) -> Union[Dict[str, Any], bool]:
        """获取账号信息"""
        url = "https://pan.quark.cn/account/info"
        response = await self._send_request(
            "GET",
            url,
            params={"fr": "pc", "platform": "pc"}
        )
        return response.get("data", False)

    async def get_file_list(self, dir_id: str = "0", page: int = 1, size: int = 50) -> Dict[str, Any]:
        """
        获取文件列表
        :param dir_id: 文件夹 ID，默认为根目录
        :param page: 页码
        :param size: 每页数量
        """
        url = f"{self.BASE_URL}/1/clouddrive/file/sort"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "pdir_fid": dir_id,
            "_page": page,
            "_size": size,
            "_fetch_total": "1",
            "_fetch_sub_dirs": "0",
            "_sort": "file_type:asc,updated_at:desc"
        }
        return await self._send_request("GET", url, params=params)

    async def search_files(self, keyword: str, dir_id: str = "0") -> Dict[str, Any]:
        """
        搜索文件
        :param keyword: 搜索关键词
        :param dir_id: 搜索目录 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/file/search"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "pdir_fid": dir_id,
            "query": keyword
        }
        return await self._send_request("GET", url, params=params)

    async def get_download_url(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件下载链接
        :param file_id: 文件 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/file/download"
        params = {"pr": "ucpro", "fr": "pc"}
        data = {"fids": [file_id]}
        return await self._send_request("POST", url, params=params, json=data)

    async def create_folder(self, name: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        创建文件夹
        :param name: 文件夹名称
        :param parent_id: 父文件夹 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/file"
        params = {"pr": "ucpro", "fr": "pc"}
        data = {
            "pdir_fid": parent_id,
            "file_name": name,
            "dir_init_lock": False
        }
        return await self._send_request("POST", url, params=params, json=data)

    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """
        重命名文件/文件夹
        :param file_id: 文件/文件夹 ID
        :param new_name: 新名称
        """
        url = f"{self.BASE_URL}/1/clouddrive/file/rename"
        params = {"pr": "ucpro", "fr": "pc"}
        data = {"fid": file_id, "file_name": new_name}
        return await self._send_request("POST", url, params=params, json=data)

    async def delete_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        删除文件/文件夹
        :param file_ids: 文件/文件夹 ID 列表
        """
        url = f"{self.BASE_URL}/1/clouddrive/file/delete"
        params = {"pr": "ucpro", "fr": "pc"}
        data = {
            "action_type": 2,
            "filelist": file_ids,
            "exclude_fids": []
        }
        return await self._send_request("POST", url, params=params, json=data)

    async def get_share_info(self, share_id: str, password: str = "") -> Dict[str, Any]:
        """
        获取分享信息
        :param share_id: 分享 ID
        :param password: 分享密码
        """
        url = f"{self.BASE_URL}/1/clouddrive/share/sharepage/token"
        params = {"pr": "ucpro", "fr": "pc"}
        data = {"pwd_id": share_id, "passcode": password}
        return await self._send_request("POST", url, params=params, json=data)

    async def get_share_file_list(self, share_id: str, token: str, dir_id: str = "0") -> Dict[str, Any]:
        """
        获取分享文件列表
        :param share_id: 分享 ID
        :param token: 分享 token
        :param dir_id: 文件夹 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/share/sharepage/detail"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "pwd_id": share_id,
            "stoken": token,
            "pdir_fid": dir_id,
            "_fetch_share": "1",
            "_fetch_total": "1"
        }
        return await self._send_request("GET", url, params=params)

    async def save_share_files(self, share_id: str, token: str, file_ids: List[str],
                        file_tokens: List[str], target_dir_id: str = "0") -> Dict[str, Any]:
        """
        保存分享文件
        :param share_id: 分享 ID
        :param token: 分享 token
        :param file_ids: 文件 ID 列表
        :param file_tokens: 文件 token 列表
        :param target_dir_id: 目标文件夹 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/share/sharepage/save"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "__dt": int(random.uniform(1, 5) * 60 * 1000),
            "__t": datetime.now().timestamp()
        }
        data = {
            "fid_list": file_ids,
            "fid_token_list": file_tokens,
            "to_pdir_fid": target_dir_id,
            "pwd_id": share_id,
            "stoken": token,
            "scene": "link"
        }
        return await self._send_request("POST", url, params=params, json=data)

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        :param task_id: 任务 ID
        """
        url = f"{self.BASE_URL}/1/clouddrive/task"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "task_id": task_id,
            "__dt": int(random.uniform(1, 5) * 60 * 1000),
            "__t": datetime.now().timestamp()
        }
        return await self._send_request("GET", url, params=params)

    def wait_task_complete(self, task_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        等待任务完成
        :param task_id: 任务 ID
        :param timeout: 超时时间（秒）
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return {"code": -1, "message": "任务超时"}

            response = self.get_task_status(task_id)
            if response["data"]["status"] != 0:
                return response
            
            time.sleep(0.5)

    def extract_share_info(self, share_url: str) -> Dict[str, Any]:
        """
        从分享链接中提取信息
        :param share_url: 分享链接
        """
        info = {
            "share_id": None,
            "password": None,
            "dir_id": "0",
            "paths": []
        }
        
        # 提取分享 ID
        match_id = re.search(r"/s/(\w+)", share_url)
        if match_id:
            info["share_id"] = match_id.group(1)
            
        # 提取密码
        match_pwd = re.search(r"pwd=(\w+)", share_url)
        if match_pwd:
            info["password"] = match_pwd.group(1)
            
        # 提取路径信息
        matches = re.findall(r"/(\w{32})-?([^/]+)?", share_url)
        for match in matches:
            fid = match[0]
            name = quote_plus(match[1]).replace("*101", "-") if match[1] else None
            info["paths"].append({"fid": fid, "name": name})
            info["dir_id"] = fid  # 使用最后一个 ID 作为目录 ID
            
        return info 