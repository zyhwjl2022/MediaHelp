from typing import List, Dict, Any, Union, Optional
from loguru import logger
from .quark_sdk import QuarkSDK

class QuarkHelper:
    """夸克网盘功能助手"""

    def __init__(self, cookie: str):
        """
        初始化夸克网盘助手
        :param cookie: 夸克网盘 cookie
        """
        self.sdk = QuarkSDK(cookie)
        
    async def init(self) -> bool:
        """
        初始化并验证账号
        :return: 是否初始化成功
        """
        result = await self.sdk.init()
        if not result:
            logger.error("夸克网盘账号初始化失败，请检查 cookie 是否有效")
            return False
        logger.info(f"夸克网盘账号 [{self.sdk.nickname}] 初始化成功")
        return True

    async def list_files(self, dir_id: str = "0", recursive: bool = False) -> List[Dict[str, Any]]:
        """
        获取文件列表
        :param dir_id: 文件夹ID，默认为根目录
        :param recursive: 是否递归获取子文件夹内容
        :return: 文件列表
        """
        all_files = []
        page = 1
        while True:
            logger.info(f"获取文件列表参数：{dir_id}, {page}")
            response = await self.sdk.get_file_list(dir_id=dir_id, page=page)
            if response.get("code") != 0:
                logger.error(f"获取文件列表失败：{response.get('message')}")
                break
                
            files = response.get("data", {}).get("list", [])
            if not files:
                break
                
            all_files.extend(files)
            
            # 如果需要递归获取子文件夹
            if recursive:
                for file in files:
                    if file.get("file_type") == 1:  # 是文件夹
                        sub_files = await self.list_files(file.get("fid"), recursive=True)
                        all_files.extend(sub_files)
            
            page += 1
            
        return all_files

    async def search(self, keyword: str, dir_id: str = "0") -> List[Dict[str, Any]]:
        """
        搜索文件
        :param keyword: 搜索关键词
        :param dir_id: 搜索目录ID
        :return: 搜索结果列表
        """
        response = await self.sdk.search_files(keyword, dir_id)
        if response.get("code") != 0:
            logger.error(f"搜索文件失败：{response.get('message')}")
            return []
        return response.get("data", {}).get("list", [])

    async def get_download_info(self, file_id: str) -> Optional[Dict[str, str]]:
        """
        获取文件下载信息
        :param file_id: 文件ID
        :return: 下载信息，包含 url 和 filename
        """
        response = await self.sdk.get_download_url(file_id)
        if response.get("code") != 0:
            logger.error(f"获取下载链接失败：{response.get('message')}")
            return None
            
        data = response.get("data", [{}])[0]
        return {
            "url": data.get("download_url", ""),
            "filename": data.get("file_name", "")
        }

    async def create_dir(self, name: str, parent_id: str = "0") -> Optional[str]:
        """
        创建文件夹
        :param name: 文件夹名称
        :param parent_id: 父文件夹ID
        :return: 新建文件夹的ID
        """
        response = await self.sdk.create_folder(name, parent_id)
        if response.get("code") != 0:
            logger.error(f"创建文件夹失败：{response.get('message')}")
            return None
        return response.get("data", {}).get("fid")

    async def rename(self, file_id: str, new_name: str) -> bool:
        """
        重命名文件或文件夹
        :param file_id: 文件/文件夹ID
        :param new_name: 新名称
        :return: 是否成功
        """
        response = await self.sdk.rename_file(file_id, new_name)
        if response.get("code") != 0:
            logger.error(f"重命名失败：{response.get('message')}")
            return False
        return True

    async def delete(self, file_ids: Union[str, List[str]]) -> bool:
        """
        删除文件或文件夹
        :param file_ids: 单个文件ID或文件ID列表
        :return: 是否成功
        """
        if isinstance(file_ids, str):
            file_ids = [file_ids]
            
        response = await self.sdk.delete_files(file_ids)
        if response.get("code") != 0:
            logger.error(f"删除文件失败：{response.get('message')}")
            return False
        return True

    async def get_fids(self, file_paths: str) -> List[Dict[str, Any]]:
        """
        获取文件路径对应的 fid
        :param file_paths: 文件路径列表
        :return: 文件路径和 fid 的对应关系列表，每个元素包含 file_path 和 fid
        """
        return await self.sdk.get_fids(file_paths)

    async def save_shared_files(self, share_url: str, password: str = "", 
                              target_dir: str = "0") -> bool:
        """
        保存分享文件到网盘
        :param share_url: 分享链接
        :param password: 分享密码
        :param target_dir: 保存到的目标文件夹ID
        :return: 是否成功
        """
        # 解析分享链接
        share_info = self.sdk.extract_share_info(share_url)
        if not share_info["share_id"]:
            logger.error("无效的分享链接")
            return False
            
        # 获取分享信息
        share_response = await self.sdk.get_share_info(
            share_info["share_id"], 
            password or share_info["password"]
        )
        if share_response.get("code") != 0:
            logger.error(f"获取分享信息失败：{share_response.get('message')}")
            return False
            
        token = share_response.get("data", {}).get("token")
        if not token:
            return False
            
        # 获取分享文件列表
        file_list = await self.sdk.get_share_file_list(
            share_info["share_id"],
            token,
            share_info["dir_id"]
        )
        if file_list.get("code") != 0:
            logger.error(f"获取分享文件列表失败：{file_list.get('message')}")
            return False
            
        files = file_list.get("data", {}).get("list", [])
        if not files:
            logger.warning("分享文件列表为空")
            return False
            
        # 保存文件
        file_ids = [f["fid"] for f in files]
        file_tokens = [f.get("share_fid_token", "") for f in files]
        
        save_response = await self.sdk.save_share_files(
            share_info["share_id"],
            token,
            file_ids,
            file_tokens,
            target_dir
        )
        
        if save_response.get("code") != 0:
            logger.error(f"保存分享文件失败：{save_response.get('message')}")
            return False
            
        return True 