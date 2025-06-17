# 夸克网盘自动保存任务
import asyncio
import re
from typing import Any, Dict
from loguru import logger
from utils import config_manager, scheduled_manager
from utils.magic_rename import MagicRename
from utils.quark_helper import QuarkHelper

class QuarkAutoSave:
    helper = None
    task_name = ""
    params = {}
    task = {}
    savepath_fid = {"/": "0"}
    
  
    def __init__(self):
        try:
            # 从系统配置中获取 cookie
            sys_config = config_manager.config_manager.get_config()
            cookie = sys_config.get("quarkCookie", "")
            if not cookie:
                logger.error(f"任务 [{self.task_name}] 未配置夸克网盘 cookie")
                return
            self.helper= QuarkHelper(cookie)
        except Exception as e:
            logger.error(f"任务 [{self.task_name}] 夸克网盘helper获取失败: {str(e)}")
            return
    
    async def get_dir_fid(self, dir_name: str):
        """获取目录fid"""
        savepath = re.sub(r"/{2,}", "/", f"/{dir_name}")
        if not self.savepath_fid.get(savepath):
            if get_fids := await self.helper.sdk.get_fids([savepath]):
                self.savepath_fid[savepath] = get_fids[0]["fid"]
            else:
                return None
        to_pdir_fid = self.savepath_fid[savepath]
        return to_pdir_fid

    async def dir_check_and_save(self, pwd_id, stoken, pdir_fid="", subdir_path=""):
        target_dir = self.params.get("targetDir", "/")
        start_magic = self.params.get("startMagic", [])
        if not isinstance(start_magic, list):
            start_magic = [start_magic] if start_magic else []
              
        # 获取分享文件列表
        file_list = await self.helper.sdk.get_share_file_list(
          pwd_id,
          stoken,
          pdir_fid
        )
    
        if file_list.get("code") != 0:
            logger.error(f"获取分享文件列表失败: {file_list.get('message')}")
            return

        files = file_list.get("data", {}).get("list", [])
        
        # 获取分享文件列表 如果只有一个目录 自动读取目录内列表
        if not files:
          if subdir_path == "":
            logger.warning("分享文件列表为空")
          return []
        # elif(len(files) == 1 and files[0].get("dir") and subdir_path == ""):
        #   logger.info("🧠 该分享是一个文件夹，创建这个文件夹")
        #   file_list = await self.helper.sdk.get_share_file_list( pwd_id, stoken, files[0]["fid"])
        #   if file_list.get("code") != 0:
        #     logger.error(f"获取分享文件列表失败: {file_list.get('message')}")
        #     return
        #   files = file_list.get("data", {}).get("list", [])

        # 获取目标文件夹的fid
        to_pdir_fid = await self.get_dir_fid(f"{target_dir}{subdir_path}")
        if not to_pdir_fid:
            logger.error(f"❌ 目录 {target_dir}{subdir_path} fid获取失败，跳过转存")
            return
        logger.info(f"获取目标文件夹fid成功: {to_pdir_fid}")
    
        # 获取目标文件夹中的文件列表，用于查重
        target_files = await self.helper.sdk.get_file_list(to_pdir_fid, recursive=True)
        if target_files.get("code") != 0:
            logger.error(f"获取目标文件夹文件列表失败: {target_files.get('message')}")
            return

        target_file_list = target_files.get("data", {}).get("list", [])

        logger.info(f"target_file_list: {len(target_file_list)}")
        logger.info(f"files: {len(files)}")

        # 需要保存的文件
        need_save_files = []
        # 文件判重
        mr = MagicRename(scheduled_manager.scheduled_manager.get_config().get("magic_regex", {}))
        mr.set_taskname(self.task_name)
         # 魔法正则转换
        pattern, replace = mr.magic_regex_conv(
            self.params.get("pattern", "$TV_PRO"), self.params.get("replace", "")
        )
        dir_name_list = [dir_file["file_name"] for dir_file in target_file_list]
        for share_file in files:
            search_pattern = (
                self.params.get("search_pattern", "") if share_file["dir"] else pattern
            )
            if re.search(search_pattern, share_file["file_name"]):
              if not share_file["dir"]:
                # 文件
                # 正则文件名匹配  选择那些需要保存的文件
                should_save = True
                if start_magic:
                    should_save = mr.start_magic_is_save(start_magic, share_file["file_name"])
                # 判断原文件名是否存在，处理忽略扩展名
                if (not mr.is_exists(
                    share_file["file_name"],
                    dir_name_list,
                    (self.params.get("ignore_extension")),
                ) and should_save):
                    # 替换后的文件名
                    file_name_re = mr.sub(pattern, replace, share_file["file_name"])
                    # 判断替换后的文件名是否存在
                    if not mr.is_exists(
                        file_name_re,
                        dir_name_list,
                        self.params.get("ignore_extension"),
                    ):
                        share_file["file_name_re"] = file_name_re
                        need_save_files.append(share_file)
              else:
                # 文件夹
                # 创建文件夹
                # 判断文件夹存不存在
                to_pdir_fid2 = await self.get_dir_fid(f"{target_dir}{subdir_path}/{share_file['file_name']}")
                if not to_pdir_fid2:
                  await self.helper.sdk.create_folder(share_file["file_name"], to_pdir_fid)
                await self.dir_check_and_save(pwd_id, stoken, share_file["fid"],subdir_path= f"{subdir_path}/{share_file['file_name']}")        
        # 保存文件
        if need_save_files:
            logger.info(f"开始保存 {len(need_save_files)} 个文件到目录")
            file_ids = [file["fid"] for file in need_save_files]
            file_tokens = [file["share_fid_token"] for file in need_save_files]
            save_result = await self.helper.sdk.save_share_files(
              pwd_id,
              stoken,
              file_ids,
              file_tokens,
              to_pdir_fid
            )
            if save_result.get("code") != 0:
              logger.error(f"文件保存失败: {save_result.get('message')}")
              return
            logger.info(f"文件保存成功: {save_result}")
            
            task_id = save_result.get("data", {}).get("task_id")

            task_status = await self.helper.sdk.get_task_status(task_id)
                
            if task_status.get("code") == 0:
              saved_fid = task_status.get("data", {}).get("save_as", {}).get("save_as_top_fids", [])
              for i, file in enumerate(need_save_files):
                try:
                  # 如果需要重命名
                  if file.get("file_name_re") and file["file_name_re"] != file["file_name"]:
                    # 执行重命名
                    rename_result = await self.helper.sdk.rename_file(
                      saved_fid[i],
                      file["file_name_re"]
                    )
                    # 为了防止封控 间隔0.5秒
                    await asyncio.sleep(0.5)
                    if rename_result.get("code") != 0:
                      logger.error(f"文件 {file['file_name']} 重命名失败: {rename_result.get('message')}")
                      continue

                    logger.success(f"文件 {file['file_name']} 已保存并重命名为 {file['file_name_re']}")
                  else:
                    logger.success(f"文件 {file['file_name']} 保存成功")
        
                except Exception as e:
                  logger.error(f"处理文件 {file['file_name']} 时发生错误: {str(e)}")
                  continue
            else:
              logger.error(f"任务 {task_id} 获取失败: {task_status.get('message')}")
              return
        else:
          logger.info("没有需要保存的文件")        

    async def quark_auto_save(self, task: Dict[str, Any]):
        """夸克网盘自动保存任务
        参数:
        1. shareUrl: 分享链接
        2. targetDir: 目标文件夹ID，默认为根目录
        3. sourcePath: 源路径，默认为根目录
        """
        self.task = task
        self.params = task.get("params", {})
        self.task_name = task.get("name", "")
        share_url = self.params.get("shareUrl")
        target_dir = self.params.get("targetDir", "/")
        isShareUrlValid = self.params.get("isShareUrlValid", True)

        if not isShareUrlValid:
            logger.error(f"任务 [{self.task_name}] 分享链接无效: {share_url} 跳过执行")
            return
        if not share_url:
            logger.error(f"任务 [{self.task_name}] 缺少必要参数: shareUrl")
            return
        if not target_dir:
            logger.error(f"任务 [{self.task_name}] 缺少必要参数: targetDir")
            return

        ## 验证cookie是否有效
        if not await self.helper.init():
            logger.error(f"任务 [{self.task_name}] 夸克网盘初始化失败，请检查 cookie 是否有效")
            return
        # 获取分享信息 看看分享链接是否有效
        # 解析分享链接
        share_info = self.helper.sdk.extract_share_info(share_url)
        if not share_info["share_id"]:
           logger.error(f"分享链接无效: {share_url}")
           # 创建新的任务对象进行更新
           updated_task = task.copy()
           updated_task["params"] = task.get("params", {}).copy()
           updated_task["params"]["isShareUrlValid"] = False
           scheduled_manager.update_task(self.task_name, updated_task)
           return
        # 获取分享信息
        share_response = await self.helper.sdk.get_share_info(
            share_info["share_id"], 
            share_info["password"]
        )
        if share_response.get("code") != 0:
            logger.error(f"分享链接无效: {share_url}")
            # 创建新的任务对象进行更新
            updated_task = task.copy()
            updated_task["params"] = task.get("params", {}).copy()
            updated_task["params"]["isShareUrlValid"] = False
            scheduled_manager.update_task(self.task_name, updated_task)
            return

        # 获取分享文件列表
        token = share_response.get("data", {}).get("stoken")
        if not token:
            logger.error(f"获取分享token失败: {share_response}")
            return
        
        await self.dir_check_and_save(share_info["share_id"], token,share_info['dir_id'])
        

