# 天翼云盘自动保存任务
from typing import Any, Dict
from loguru import logger
from utils.cloud189.client import Cloud189Client

class Cloud189AutoSave:
    client = {}
    params = {}
    task = {}
    task_name = ""
    def __init__(self):
      # 创建客户端实例，它会自动从配置文件加载session
      self.client = Cloud189Client()
    async def dir_check_and_save(self, share_info, file_id = ''):
      target_dir = self.params.get("targetDir", "-11")

      # 获取分享文件列表
      filesResponse = await self.client.list_share_files(
        share_id=share_info["shareId"],
        file_id= file_id if file_id else share_info["fileId"],
        share_mode=share_info.get("shareMode", "1"),
        access_code=share_info.get("accessCode", ""),
        is_folder=share_info.get("isFolder", "")
      )
        
      files = filesResponse.get("fileListAO", {}).get("fileList", [])
      folders = filesResponse.get("fileListAO", {}).get("folderList", [])
      
      #获取目标文件列表
      target_response = await self.client.list_files(target_dir)
      target_files = target_response.get("fileListAO", {}).get("fileList", [])
      target_folders = target_response.get("fileListAO", {}).get("folderList", [])
      
      logger.info(f"目标文件列表: {len(target_files)}")
      logger.info(f"目标文件夹列表: {len(target_folders)}")
      logger.info(f"分享文件列表: {len(files)}")
      logger.info(f"分享文件夹列表: {len(folders)}")


    async def cloud189_auto_save(self, task: Dict[str, Any]):
        """天翼云盘自动保存任务
        参数:
        1. shareUrl: 分享链接
        2. targetDir: 目标文件夹ID，默认为-11
        3. others: 其他参数
        """
        self.task = task
        self.params = task.get("params", {})
        self.task_name = task.get("name", "")
        target_dir = self.params.get("targetDir", "-11")
        share_url = self.params.get("shareUrl")

        if not share_url:
            logger.error("缺少必要参数: shareUrl")
            return
        
        if not target_dir:
            logger.error("缺少必要参数: targetDir")
            return
        # 验证账号登录
        if not await self.client.login():
            logger.error("天翼云盘登录失败")
            return
        # TODO: 后续的转存逻辑
        # 获取分享信息
        # 解析分享链接
        logger.info(f"解析分享链接: {share_url}")
        url, _ = self.client.parse_cloud_share(share_url)
        if not url:
            logger.error("无效的分享链接")
            return
        # 获取分享码
        share_code = self.client.parse_share_code(url)
            
        # 获取分享信息
        share_info = await self.client.get_share_info(share_code)
        await self.dir_check_and_save(share_info)
        


