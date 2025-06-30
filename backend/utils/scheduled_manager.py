import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
import croniter

class ScheduledManager:
    _instance = None
    _config: Dict[str, Any] = {}
    _default_config = {
        "magic_regex": {
            "$TV": {
                "pattern": r".*?([Ss]\d{1,2})?(?:[第EePpXx\.\-\_\( ]{1,2}|^)(\d{1,3})(?!\d).*?\.(mp4|mkv)",
                "replace": r"\1E\2.\3"
            },
            "$BLACK_WORD": {
                "pattern": r"^(?!.*纯享)(?!.*加更)(?!.*超前企划)(?!.*训练室)(?!.*蒸蒸日上).*",
                "replace": ""
            },
            "$SHOW_PRO": {
                "pattern": r"^(?!.*纯享)(?!.*加更)(?!.*抢先)(?!.*预告).*?第\d+期.*",
                "replace": "{II}.{TASKNAME}.{DATE}.第{E}期{PART}.{EXT}"
            },
            "$TV_PRO": {
                "pattern": "",
                "replace": "{TASKNAME}.{SXX}E{E}.{EXT}" 
            }
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScheduledManager, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        """初始化配置"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        self._config_file = os.path.join(config_dir, "scheduled.yaml")

        # 创建配置目录
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # 读取或创建配置文件
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
                self._config = {}
        else:
            self._config = {}

        # 使用默认配置补充缺失的配置项
        self._ensure_default_config()

    def _ensure_default_config(self):
        """确保所有默认配置项都存在"""
        is_modified = False
        
        if not self._config:
            self._config = {}
            
        # 检查并添加 magic_regex 配置
        if "magic_regex" not in self._config:
            # 从YAML文件中读取magic_regex配置
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f) or {}
                    if "magic_regex" in yaml_config:
                        self._config["magic_regex"] = yaml_config["magic_regex"]
                    else:
                        # 如果YAML文件中没有magic_regex配置，则使用默认配置
                        self._config["magic_regex"] = self._default_config["magic_regex"]
            except Exception as e:
                logger.error(f"读取YAML文件中的magic_regex配置失败: {e}")
                # 读取失败时使用默认配置
                self._config["magic_regex"] = self._default_config["magic_regex"]
            is_modified = True

        if is_modified:
            self._save_config()

    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config

    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return self._config.get("tasks", [])

    def get_enabled_tasks(self) -> List[Dict[str, Any]]:
        """获取所有启用的任务"""
        return [task for task in self.get_tasks() if task.get("enabled", False)]

    def get_task_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取任务"""
        for task in self.get_tasks():
            if task.get("name") == name:
                return task
        return None

    def add_task(self, task: Dict[str, Any]) -> bool:
        """添加任务"""
        try:
            # 验证必要字段
            required_fields = ["name", "cron", "task"]
            for field in required_fields:
                if field not in task:
                    logger.error(f"任务缺少必要字段: {field}")
                    return False

            # 验证cron表达式
            try:
                croniter.croniter(task["cron"])
            except ValueError as e:
                logger.error(f"无效的cron表达式: {e}")
                return False

            # 检查任务名称是否已存在
            if self.get_task_by_name(task["name"]):
                logger.error(f"任务名称已存在: {task['name']}")
                return False

            # 设置默认值
            if "enabled" not in task:
                task["enabled"] = True
            if "params" not in task:
                task["params"] = {}

            # 添加任务
            if "tasks" not in self._config:
                self._config["tasks"] = []
            self._config["tasks"].append(task)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False

    def update_task(self, name: str, task: Dict[str, Any]) -> bool:
        """更新任务"""
        try:
            tasks = self.get_tasks()
            for i, existing_task in enumerate(tasks):
                if existing_task.get("name") == name:
                    # 验证cron表达式
                    if "cron" in task:
                        try:
                            croniter.croniter(task["cron"])
                        except ValueError as e:
                            logger.error(f"无效的cron表达式: {e}")
                            return False

                    # 更新任务
                    tasks[i].update(task)
                    self._save_config()
                    return True
            logger.error(f"任务不存在: {name}")
            return False
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False

    def delete_task(self, name: str) -> bool:
        """删除任务"""
        try:
            tasks = self.get_tasks()
            for i, task in enumerate(tasks):
                if task.get("name") == name:
                    tasks.pop(i)
                    self._save_config()
                    return True
            logger.error(f"任务不存在: {name}")
            return False
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False

    def enable_task(self, name: str) -> bool:
        """启用任务"""
        return self.update_task(name, {"enabled": True})

    def disable_task(self, name: str) -> bool:
        """禁用任务"""
        return self.update_task(name, {"enabled": False})

    def enable_task_down_load(self, name: str) -> bool:
        """启用任务下载"""
        return self.update_task(name, {"is_down_load": True})

    def disable_task_down_load(self, name: str) -> bool:
        """禁用任务下载"""
        return self.update_task(name, {"is_down_load": False})

    def get_next_run_time(self, task: Dict[str, Any]) -> Optional[datetime]:
        """获取任务下次运行时间"""
        try:
            cron = task.get("cron")
            if not cron:
                return None
            
            cron_iter = croniter.croniter(cron, datetime.now())
            return cron_iter.get_next(datetime)
        except Exception as e:
            logger.error(f"获取下次运行时间失败: {e}")
            return None

# 创建全局实例
scheduled_manager = ScheduledManager() 