import json
import inspect
import traceback
import os
from typing import Optional, Dict, Any, List
from loguru import logger
from datetime import datetime, timedelta
from schemas.log import LogEntry, LogQuery, LogStats, LogListResponse
import asyncio
from pathlib import Path

class FileLoggerService:
    """基于文件的日志服务类"""
    
    def __init__(self, log_file_path: str = "logs/app.log", max_file_size: int = 10 * 1024 * 1024):  # 10MB
        self.log_file_path = Path(log_file_path)
        self.max_file_size = max_file_size
        self._ensure_log_directory()
        self._lock = asyncio.Lock()
    
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_caller_info(self) -> tuple[str, str, int]:
        """获取调用者信息"""
        try:
            frame = inspect.currentframe()
            # 跳过当前函数和loguru的调用
            for _ in range(3):
                frame = frame.f_back
            
            if frame:
                module = frame.f_globals.get('__name__', 'unknown')
                function = frame.f_code.co_name
                line = frame.f_lineno
                return module, function, line
        except Exception:
            pass
        
        return 'unknown', 'unknown', 0
    
    async def _write_log_to_file(self, log_entry: LogEntry):
        """将日志写入文件"""
        async with self._lock:
            try:
                # 检查文件大小，如果超过限制则轮转
                if self.log_file_path.exists() and self.log_file_path.stat().st_size > self.max_file_size:
                    await self._rotate_log_file()
                
                # 格式化日志条目
                log_line = self._format_log_entry(log_entry)
                
                # 写入文件
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_line + '\n')
                    
            except Exception as e:
                logger.error(f"写入日志文件失败: {e}")
    
    def _format_log_entry(self, log_entry: LogEntry) -> str:
        """格式化日志条目为JSON字符串"""
        log_dict = log_entry.model_dump()
        return json.dumps(log_dict, ensure_ascii=False, default=str)
    
    async def _rotate_log_file(self):
        """轮转日志文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.log_file_path.with_suffix(f".{timestamp}.log")
            
            if self.log_file_path.exists():
                self.log_file_path.rename(backup_path)
                
            # 保留最近10个备份文件
            await self._cleanup_old_logs()
            
        except Exception as e:
            logger.error(f"轮转日志文件失败: {e}")
    
    async def _cleanup_old_logs(self, keep_count: int = 10):
        """清理旧的日志文件"""
        try:
            log_dir = self.log_file_path.parent
            pattern = f"{self.log_file_path.stem}.*.log"
            
            log_files = sorted(
                log_dir.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # 删除超出保留数量的旧文件
            for old_file in log_files[keep_count:]:
                old_file.unlink()
                
        except Exception as e:
            logger.error(f"清理旧日志文件失败: {e}")
    
    async def log(
        self,
        level: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        save_to_file: bool = True
    ):
        """记录日志"""
        # 获取调用者信息
        module, function, line = self._get_caller_info()
        
        # 创建日志条目
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level.upper(),
            message=message,
            module=module,
            function=function,
            line=line,
            extra_data=extra_data
        )
        
        # 记录到控制台
        log_message = f"[{module}.{function}:{line}] {message}"
        if extra_data:
            log_message += f" | Extra: {json.dumps(extra_data, ensure_ascii=False)}"
        
        if level.upper() == "DEBUG":
            logger.debug(log_message)
        elif level.upper() == "INFO":
            logger.info(log_message)
        elif level.upper() == "WARNING":
            logger.warning(log_message)
        elif level.upper() == "ERROR":
            logger.error(log_message)
        elif level.upper() == "CRITICAL":
            logger.critical(log_message)
        else:
            logger.info(log_message)
        
        # 记录到文件
        if save_to_file:
            await self._write_log_to_file(log_entry)
    
    async def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        await self.log("DEBUG", message, **kwargs)
    
    async def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        await self.log("INFO", message, **kwargs)
    
    async def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        await self.log("WARNING", message, **kwargs)
    
    async def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        await self.log("ERROR", message, **kwargs)
    
    async def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        await self.log("CRITICAL", message, **kwargs)
    
    async def exception(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """记录异常日志"""
        if exc_info:
            error_details = traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
            error_message = f"{message}\n{''.join(error_details)}"
        else:
            error_message = f"{message}\n{traceback.format_exc()}"
        
        await self.log("ERROR", error_message, **kwargs)
    
    async def read_logs(self, query: LogQuery) -> LogListResponse:
        """读取日志文件并过滤"""
        try:
            if not self.log_file_path.exists():
                return LogListResponse(items=[], total=0, page=1, page_size=query.page_size, total_pages=0)
            
            logs = []
            async with self._lock:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_dict = json.loads(line)
                            log_entry = LogEntry(**log_dict)
                            
                            # 应用过滤条件
                            if self._matches_filter(log_entry, query):
                                logs.append(log_entry)
                        except Exception as e:
                            logger.warning(f"解析日志行失败: {e}, 行内容: {line}")
            
            # 排序
            if query.order_desc:
                logs.sort(key=lambda x: x.timestamp, reverse=True)
            else:
                logs.sort(key=lambda x: x.timestamp)
            
            # 分页
            total = len(logs)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            page_logs = logs[start_idx:end_idx]
            
            total_pages = (total + query.page_size - 1) // query.page_size
            
            return LogListResponse(
                items=page_logs,
                total=total,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
            return LogListResponse(items=[], total=0, page=1, page_size=query.page_size, total_pages=0)
    
    def _matches_filter(self, log_entry: LogEntry, query: LogQuery) -> bool:
        """检查日志条目是否匹配过滤条件"""
        if query.level and log_entry.level != query.level:
            return False
        
        if query.module and log_entry.module != query.module:
            return False
        
        if query.start_time and log_entry.timestamp < query.start_time:
            return False
        
        if query.end_time and log_entry.timestamp > query.end_time:
            return False
        
        if query.message_contains and query.message_contains.lower() not in log_entry.message.lower():
            return False
        
        return True
    
    async def get_stats(self) -> LogStats:
        """获取日志统计信息"""
        try:
            if not self.log_file_path.exists():
                return LogStats(
                    total_count=0, error_count=0, warning_count=0, info_count=0, debug_count=0,
                    today_count=0, yesterday_count=0, level_distribution={}, module_distribution={}
                )
            
            level_distribution = {}
            module_distribution = {}
            total_count = 0
            today_count = 0
            yesterday_count = 0
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            async with self._lock:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_dict = json.loads(line)
                            log_entry = LogEntry(**log_dict)
                            
                            total_count += 1
                            
                            # 统计级别分布
                            level_distribution[log_entry.level] = level_distribution.get(log_entry.level, 0) + 1
                            
                            # 统计模块分布
                            if log_entry.module:
                                module_distribution[log_entry.module] = module_distribution.get(log_entry.module, 0) + 1
                            
                            # 统计今日和昨日数量
                            log_date = log_entry.timestamp.date()
                            if log_date == today:
                                today_count += 1
                            elif log_date == yesterday:
                                yesterday_count += 1
                                
                        except Exception:
                            continue
            
            return LogStats(
                total_count=total_count,
                error_count=level_distribution.get("ERROR", 0),
                warning_count=level_distribution.get("WARNING", 0),
                info_count=level_distribution.get("INFO", 0),
                debug_count=level_distribution.get("DEBUG", 0),
                today_count=today_count,
                yesterday_count=yesterday_count,
                level_distribution=level_distribution,
                module_distribution=module_distribution
            )
            
        except Exception as e:
            logger.error(f"获取日志统计失败: {e}")
            return LogStats(
                total_count=0, error_count=0, warning_count=0, info_count=0, debug_count=0,
                today_count=0, yesterday_count=0, level_distribution={}, module_distribution={}
            )
    
    async def get_modules(self) -> List[str]:
        """获取所有模块名称"""
        try:
            if not self.log_file_path.exists():
                return []
            
            modules = set()
            async with self._lock:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_dict = json.loads(line)
                            log_entry = LogEntry(**log_dict)
                            if log_entry.module:
                                modules.add(log_entry.module)
                        except Exception:
                            continue
            
            return sorted(list(modules))
            
        except Exception as e:
            logger.error(f"获取模块列表失败: {e}")
            return []
    
    async def get_levels(self) -> List[str]:
        """获取所有日志级别"""
        try:
            if not self.log_file_path.exists():
                return []
            
            levels = set()
            async with self._lock:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_dict = json.loads(line)
                            log_entry = LogEntry(**log_dict)
                            levels.add(log_entry.level)
                        except Exception:
                            continue
            
            return sorted(list(levels))
            
        except Exception as e:
            logger.error(f"获取日志级别列表失败: {e}")
            return []
    
    async def clear_logs(self) -> int:
        """清空日志文件"""
        try:
            async with self._lock:
                if self.log_file_path.exists():
                    # 备份当前日志文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = self.log_file_path.with_suffix(f".{timestamp}.log")
                    self.log_file_path.rename(backup_path)
                    
                    # 创建新的空日志文件
                    self.log_file_path.touch()
                    
                    return 1  # 表示清空了一个文件
                return 0
                
        except Exception as e:
            logger.error(f"清空日志文件失败: {e}")
            return 0

# 创建全局日志服务实例
logger_service = FileLoggerService()

# 便捷函数，用于同步代码中调用
def log_sync(level: str, message: str, **kwargs):
    """同步日志记录函数"""
    asyncio.create_task(logger_service.log(level, message, **kwargs))

def debug_sync(message: str, **kwargs):
    """同步DEBUG日志记录"""
    asyncio.create_task(logger_service.debug(message, **kwargs))

def info_sync(message: str, **kwargs):
    """同步INFO日志记录"""
    asyncio.create_task(logger_service.info(message, **kwargs))

def warning_sync(message: str, **kwargs):
    """同步WARNING日志记录"""
    asyncio.create_task(logger_service.warning(message, **kwargs))

def error_sync(message: str, **kwargs):
    """同步ERROR日志记录"""
    asyncio.create_task(logger_service.error(message, **kwargs))

def exception_sync(message: str, exc_info: Optional[Exception] = None, **kwargs):
    """同步异常日志记录"""
    asyncio.create_task(logger_service.exception(message, exc_info, **kwargs)) 