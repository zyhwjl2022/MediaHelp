import asyncio
from datetime import datetime
from typing import Dict, Any, Callable
from loguru import logger
import re
from task import cloud189_auto_save, quark_auto_save
from utils.scheduled_manager import scheduled_manager

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

        self.register_task_handler("quark_auto_save", quark_auto_save.QuarkAutoSave().quark_auto_save)
        self.register_task_handler("cloud189_auto_save", cloud189_auto_save.Cloud189AutoSave().cloud189_auto_save)

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
                        # 创建新的任务协程 异步执行
                        # asyncio.create_task(self._execute_task(task))
                        # 同步等待任务执行完成
                        await self._execute_task(task)

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