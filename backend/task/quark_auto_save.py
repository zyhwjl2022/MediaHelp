# 夸克网盘自动保存任务
import asyncio
import re
from typing import Any, Dict
from loguru import logger
from utils import config_manager, emby_manager, logger_service, scheduled_manager
from utils.magic_rename import MagicRename
from utils.quark_helper import QuarkHelper
import sys
sys.path.insert(0, sys.path[0]+"/../")
from utils.tg_resource_sdk import tg_resource
from api.tg_resource import organize_search_results
from utils.down_load_to_fn import fn_os

class QuarkAutoSave:
    helper = None
    task_name = ""
    params = {}
    task = {}
    savepath_fid = {"/": "0"}
    need_save_files_global = []
    down_load_result_msg = ""
    
  
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
        target_dir = self.params.get("targetDir")
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
        
        if not subdir_path:
           files[0]['file_name'] = self.task_name

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
        # logger.info(f"获取目标文件夹fid成功: {to_pdir_fid}")
    
        # 获取目标文件夹中的文件列表，用于查重
        target_files = await self.helper.sdk.get_file_list(to_pdir_fid, recursive=True)
        if target_files.get("code") != 0:
            logger.error(f"获取目标文件夹文件列表失败: {target_files.get('message')}")
            return

        target_file_list = target_files.get("data", {}).get("list", [])

        # logger.info(f"target_file_list: {len(target_file_list)}")
        # logger.info(f"files: {len(files)}")

        # 需要保存的文件
        need_save_files = []
        # 文件判重
        mr = MagicRename(scheduled_manager.scheduled_manager.get_config().get("magic_regex", {}))
        mr.set_taskname(self.task_name)
         # 魔法正则转换
        pattern, replace = mr.magic_regex_conv(
            self.params.get("pattern", ""), self.params.get("replace", "")
        )
        # logger.info(f"pattern: {pattern}")
        # logger.info(f"replace: {replace}")
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
                                     # 视频文件才进行重命名
                        if re.search(r'\.(mp4|mkv|avi|rmvb|flv|wmv|mov|m4v)$', share_file["file_name"].lower()):
                            share_file["file_name_re"] = file_name_re
                        need_save_files.append(share_file)
                        share_file['file_real_path'] = f"{target_dir}{subdir_path}/{share_file['file_name']}"
                        self.need_save_files_global.append(share_file)
                        
              else:
                # 文件夹
                # 创建文件夹
                # 判断文件夹存不存在
                to_pdir_fid2 = await self.get_dir_fid(f"{target_dir}{subdir_path}/{share_file['file_name']}")
                if not to_pdir_fid2:
                  await self.helper.sdk.create_folder(share_file["file_name"], to_pdir_fid)
                  self.need_save_files_global.append(share_file)
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
            # logger.info(f"文件保存成功: {save_result}")
            
            task_id = save_result.get("data", {}).get("task_id")

            task_status = await self.helper.sdk.get_task_status(task_id)
                
            if task_status.get("code") == 0:
              await asyncio.sleep(5)
              # #重新获取文件列表
              re_target_files = await self.helper.sdk.get_file_list(to_pdir_fid)
              if re_target_files.get("code") != 0:
                logger.error(f"获取目标文件夹文件列表失败: {re_target_files.get('message')}")
                return

              re_target_file_list = re_target_files.get("data", {}).get("list", [])
              for file in need_save_files:
                saved_fid = next((f for f in re_target_file_list if f["file_name"]==file["file_name"]), None)
                # logger.info(f"saved_fid: {saved_fid}")
                try:
                  # 如果需要重命名
                  if file.get("file_name_re") and file["file_name_re"] != file["file_name"]:
                    # 执行重命名
                    rename_result = await self.helper.sdk.rename_file(
                      saved_fid['fid'],
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
        # else:
        #   logger.info("没有需要保存的文件")        

    async def quark_auto_save(self, task: Dict[str, Any]):
        """夸克网盘自动保存任务
        参数:
        1. shareUrl: 分享链接
        2. targetDir: 目标文件夹ID，默认为根目录
        3. sourcePath: 源路径，默认为根目录
        """
        try:
          self.task = task
          self.params = task.get("params", {})
          self.task_name = task.get("name", "")
          logger_service.info_sync(f"夸克网盘自动转存任务 开始🏃‍➡️: {self.task_name} ({self.task.get('task', '')})") 
          share_url = self.params.get("shareUrl")
          target_dir = self.params.get("targetDir")
          isShareUrlValid = self.params.get("isShareUrlValid", True)
          
          # 验证cookie 是否有效
          if not await self.helper.init():
            logger.error(f"任务 [{self.task_name}] 夸克网盘初始化失败，请检查 cookie 是否有效")
            logger_service.error_sync(f"任务 [{self.task_name}] 夸克网盘初始化失败，请检查 cookie 是否有效")
            return
          if not isShareUrlValid:
              logger.error(f"任务 [{self.task_name}] 分享链接无效: {share_url} 尝试重新搜索")
              share_url = await self.get_new_url(task, share_url)
              if not share_url:
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
             updated_task['enabled'] = False
             updated_task["params"] = task.get("params", {}).copy()
             updated_task["params"]["isShareUrlValid"] = False
             scheduled_manager.scheduled_manager.update_task(self.task_name, updated_task)
             return
          # 获取分享信息
          try:
            share_response = await self.helper.sdk.get_share_info(
                share_info["share_id"], 
                share_info["password"]
            )
            if share_response.get("code") != 0:
              logger.error(f"分享链接无效: {share_url}")
              share_url = await self.get_new_url(task, share_url)
              if not share_url:
                return
              share_info = self.helper.sdk.extract_share_info(share_url)
              share_response = await self.helper.sdk.get_share_info(
                  share_info["share_id"], 
                  share_info["password"]
              )
              if share_response.get("code") != 0:
                logger.error(f"重新搜索分享链接无效: {share_url}")
                # 创建新的任务对象进行更新
                updated_task = task.copy()
                updated_task['enabled'] = False
                updated_task["params"] = task.get("params", {}).copy()
                updated_task["params"]["isShareUrlValid"] = False
                scheduled_manager.scheduled_manager.update_task(self.task_name, updated_task)
                return
          except Exception as e:
            logger.error(f"获取分享信息失败: {e}")
            # 创建新的任务对象进行更新
            updated_task = task.copy()
            updated_task['enabled'] = False
            updated_task["params"] = task.get("params", {}).copy()
            updated_task["params"]["isShareUrlValid"] = False
            scheduled_manager.scheduled_manager.update_task(self.task_name, updated_task)
            return
          # 获取分享文件列表
          token = share_response.get("data", {}).get("stoken")
          if not token:
              logger.error(f"获取分享token失败: {share_response}")
              return

          self.need_save_files_global = []
          await self.dir_check_and_save(share_info["share_id"], token,share_info['dir_id'])
            # 格式化打印需要保存的文件列表
          if self.need_save_files_global:
            # logger.info(f"夸克网盘自动转存任务 {self.task_name} ({self.task.get('task', '')}) 需要保存的文件: {self.need_save_files_global}")
            file_list_str = "\n".join([f"🎬 {file['file_name']}" + (f"\n   ↳ 将重命名为: {file['file_name_re']}" if file.get('file_name_re') else "") for file in self.need_save_files_global])
            logger_service.info_sync(f"夸克网盘自动转存任务 {self.task_name} ({self.task.get('task', '')}) 保存的文件:\n{file_list_str}")

            # 开始处理下载
            if task.get("is_down_load", False):
              logger.info(f"夸克网盘自动转存任务 {self.task_name} ({self.task.get('task', '')}) 开始下载")
              if len(self.need_save_files_global) > 0:
                  fn_os.dramaList = [
                      file['file_real_path'] 
                      for file in self.need_save_files_global 
                      if 'file_real_path' in file and file['file_real_path']
                  ]
                  fn_os.keyword = self.task_name
                  fn_os.cloud_type = "quark"
                  fn_os.cloud_file_path = None
                  down_load_result,self.down_load_result_msg = await fn_os.run_async()
              else:
                self.down_load_result_msg = "没有需要保存的文件"
            else:
               logger.error(f"夸克网盘自动转存任务 {self.task_name} ({self.task.get('task', '')}) 未启用下载")
               self.down_load_result_msg = "未启用下载"
          else:
            logger_service.info_sync(f"夸克网盘自动转存任务 {self.task_name} ({self.task.get('task', '')}) 没有需要保存的文件")
          logger_service.info_sync(f"夸克网盘自动转存任务 结束🏁: {self.task_name} ({self.task.get('task', '')})")
          return {
            "task_name": f'{self.task_name}',
            "task": self.task.get("task", ""),
            "down_load_result": self.down_load_result_msg if self.task.get("is_down_load", False) else "未启用下载",
            "need_save_files": self.need_save_files_global
          }
        except Exception as e:
          logger_service.error_sync(f"夸克网盘自动转存任务 异常🚨: {self.task_name} ({self.task.get('task', '')}) {e}")
          
    async def get_new_url(self, task: Dict[str, Any], share_url: str):
      logger.info(f"任务 [{self.task_name}] 重新搜索")
      

      results = await tg_resource.search_all(self.task_name)
      searchResult = organize_search_results(results)
      if not searchResult or 'list' not in searchResult[0] or not isinstance(searchResult[0]['list'], list) or searchResult[0]['list'] == []:
          logger.error(f"任务 [{self.task_name}] 重新搜索结果格式不正确: {searchResult}")
          return None
      searchResult = searchResult[0]['list']
      for searchItem in searchResult:
          if searchItem['cloudType'] == "quark" and searchItem['cloudLinks'] and searchItem['cloudLinks'][0]:
            share_url = searchItem['cloudLinks'][0]
            if "quark" not in share_url or self.task_name not in searchItem['title']:
                logger.error(f"任务 [{self.task_name}] 重新搜索到的链接资源不正确或不是夸克网盘链接: {share_url}")
                continue
            share_info = self.helper.sdk.extract_share_info(share_url)
            share_response = await self.helper.sdk.get_share_info(
                share_info["share_id"], 
                share_info["password"]
            )
            if share_response.get("code") == 0:
              # 创建新的任务对象进行更新
              updated_task = task.copy()
              updated_task['enabled'] = True
              updated_task["params"]["shareUrl"] = share_url
              scheduled_manager.scheduled_manager.update_task(self.task_name, updated_task)
              logger.info(f"任务 [{self.task_name}] 重新搜索到有效的分享链接: {share_url} 并更新任务")
              return share_url
            else:
                logger.error(f"任务 [{self.task_name}] 重新搜索无效分享链接: {share_url} 继续查找")
      logger.error(f"任务 [{self.task_name}] 重新搜索没有找到有效的分享链接")
      return None