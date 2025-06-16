import asyncio
from datetime import datetime
from typing import Dict, Any, Callable
from loguru import logger

from api.quark import get_share_info
from utils.scheduled_manager import scheduled_manager
from utils.config_manager import config_manager
from utils.quark_helper import QuarkHelper
from utils.cloud189.client import Cloud189Client

class TaskScheduler:
    _instance = None
    _running = False
    _task_handlers: Dict[str, Callable] = {}
    _last_run_times: Dict[str, datetime] = {}  # 记录每个任务的上次执行时间

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskScheduler, cls).__new__(cls)
        return cls._instance

    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._task_handlers[task_type] = handler

    def register_system_tasks(self):
        """注册系统默认的任务处理器"""
            
        # 夸克网盘自动保存任务
        async def quark_auto_save(task: Dict[str, Any]):
            """夸克网盘自动保存任务
            参数:
            1. shareUrl: 分享链接
            2. targetDir: 目标文件夹ID，默认为根目录
            3. sourcePath: 源路径，默认为根目录
            """
            params = task.get("params", {})
            task_name = task.get("name", "")
            share_url = params.get("shareUrl")
            target_dir = params.get("targetDir", "/媒体库")

            isShareUrlValid = params.get("isShareUrlValid", True)
            
            if not isShareUrlValid:
                logger.error(f"任务 [{task_name}] 分享链接无效: {share_url} 跳过执行")
                return

            if not share_url:
                logger.error(f"任务 [{task_name}] 缺少必要参数: shareUrl")
                return

            if not target_dir:
                logger.error(f"任务 [{task_name}] 缺少必要参数: targetDir")
                return
            try:
                # 从系统配置中获取 cookie
                sys_config = config_manager.get_config()
                cookie = sys_config.get("quarkCookie", "")
                if not cookie:
                    logger.error(f"任务 [{task_name}] 未配置夸克网盘 cookie")
                    return
                    
                helper = QuarkHelper(cookie)
                if not await helper.init():
                    logger.error(f"任务 [{task_name}] 夸克网盘初始化失败，请检查 cookie 是否有效")
                    return

            except Exception as e:
                logger.error(f"任务 [{task_name}] 夸克网盘helper获取失败: {str(e)}")
                return
              
            # 获取分享信息 看看分享链接是否有效
            # 解析分享链接
            share_info = helper.sdk.extract_share_info(share_url)
            if not share_info["share_id"]:
               logger.error(f"分享链接无效: {share_url}")
               # 创建新的任务对象进行更新
               updated_task = task.copy()
               updated_task["params"] = task.get("params", {}).copy()
               updated_task["params"]["isShareUrlValid"] = False
               scheduled_manager.update_task(task_name, updated_task)
               return
            # 获取分享信息
            logger.info(f"获取分享信息: {share_info}")
            share_response = await helper.sdk.get_share_info(
                share_info["share_id"], 
                share_info["password"]
            )
            if share_response.get("code") != 0:
                logger.error(f"分享链接无效: {share_url}")
                # 创建新的任务对象进行更新
                updated_task = task.copy()
                updated_task["params"] = task.get("params", {}).copy()
                updated_task["params"]["isShareUrlValid"] = False
                scheduled_manager.update_task(task_name, updated_task)
                return
            
            # 2.获取分享文件列表
            # 获取分享文件列表
            token = share_response.get("data", {}).get("stoken")
            if not token:
                logger.error(f"获取分享token失败: {share_response}")
                return
            file_list = await helper.sdk.get_share_file_list(
                share_info["share_id"],
                token,
                share_info["dir_id"]
            )
            
            if file_list.get("code") != 0:
                logger.error(f"获取分享文件列表失败: {file_list.get('message')}")
                return
                
            files = file_list.get("data", {}).get("list", [])
            if not files:
                logger.warning("分享文件列表为空")
                return
            
            # 获取目标文件夹的fid
            if(target_dir == "/"):
                target_dir_fid = '0'
            else:
                res = await helper.sdk.get_fids([target_dir])
                if res.get("code") != 0:
                    logger.error(f"获取目标文件夹fid失败: {res.get('message')}")
                    return
                logger.info(f"获取目标文件夹fid成功: {res}")
                # target_dir_fid = res.get("data", {})[0].get("fid", "")
              
            # logger.info(f"获取目标文件夹fid成功: {target_dir_fid}")
            
            # 根据目标文件夹的fid，获取文件列表
            # file_list = await helper.sdk.get_file_list(
            #     target_dir_fid,
            # )
            
            # logger.info(f"获取目标文件夹文件列表成功: {file_list} 来源文件列表: {files}")
            
            #保存文件
            # file_ids = [f["fid"] for f in files]
            # file_tokens = [f.get("share_fid_token", "") for f in files]
            
            # save_response = await helper.sdk.save_share_files(
            #     share_info["share_id"],
            #     share_response["data"]["token"],
            #     file_ids,
            #     file_tokens,
            #     target_dir,
            #     source_path_fid
            # )
            
            # if save_response.get("code") != 0:
            #     logger.error(f"保存分享文件失败: {save_response.get('message')}")
            #     return
                
            # logger.info(f"任务 [{task_name}] 保存分享文件成功")

        # 天翼云盘自动保存任务
        async def cloud189_auto_save(params: Dict[str, Any]):
            """天翼云盘自动保存任务
            参数:
            1. shareUrl: 分享链接
            2. targetDir: 目标文件夹ID，默认为-11
            3. others: 其他参数
            """
            share_url = params.get("shareUrl")
            target_dir = params.get("targetDir", "-11")
            others = params.get("others", {})

            if not share_url:
                logger.error("缺少必要参数: shareUrl")
                return
              
            if not target_dir:
                logger.error("缺少必要参数: targetDir")
                return

            try:
                # 创建客户端实例，它会自动从配置文件加载session
                client = Cloud189Client()
                if not await client.login():
                    logger.error("天翼云盘登录失败")
                    return

                # TODO: 后续的转存逻辑
                logger.info("成功获取天翼云盘客户端")

            except Exception as e:
                logger.error(f"天翼云盘自动保存任务失败: {str(e)}")
                return

        self.register_task_handler("quark_auto_save", quark_auto_save)
        self.register_task_handler("cloud189_auto_save", cloud189_auto_save)

        logger.info("系统任务注册完成")

    async def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        try:
            task_type = task.get("task")
            task_name = task.get("name")
            if not task_type:
                logger.error(f"任务类型未指定: {task_name}")
                return

            # 获取任务处理器
            handler = self._task_handlers.get(task_type)
            if not handler:
                logger.error(f"未找到任务处理器: {task_type}")
                return

            # 执行任务，传递完整的任务信息
            logger.info(f"开始执行任务: {task_name}")
            await handler(task)  # 修改这里，传递整个task对象而不是只传params
            # 更新上次执行时间
            self._last_run_times[task_name] = datetime.now()
            logger.info(f"任务执行完成: {task_name}")

        except Exception as e:
            logger.error(f"任务执行失败: {task_name} - {str(e)}")

    async def _check_and_execute_tasks(self):
        """检查并执行到期的任务"""
        while self._running:
            try:
                # 获取所有启用的任务
                enabled_tasks = scheduled_manager.get_enabled_tasks()
                current_time = datetime.now()

                for task in enabled_tasks:
                    task_name = task.get("name")
                    if not task_name:
                        continue

                    # 获取任务的下次执行时间
                    next_run = scheduled_manager.get_next_run_time(task)
                    if not next_run:
                        continue

                    # 检查是否需要执行
                    last_run = self._last_run_times.get(task_name)
                    if not last_run or (next_run <= current_time and last_run < next_run):
                        # 创建新的任务协程
                        asyncio.create_task(self._execute_task(task))

                # 清理已删除任务的执行记录
                task_names = {task.get("name") for task in enabled_tasks}
                removed_tasks = set(self._last_run_times.keys()) - task_names
                for task_name in removed_tasks:
                    self._last_run_times.pop(task_name, None)

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"任务检查失败: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待一分钟后继续

    async def start(self):
        """启动调度器"""
        if self._running:
            return

        # 注册系统任务
        self.register_system_tasks()
        
        self._running = True
        logger.info("定时任务调度器已启动")
        await self._check_and_execute_tasks()

    async def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("定时任务调度器已停止")

# 创建全局实例
task_scheduler = TaskScheduler() 