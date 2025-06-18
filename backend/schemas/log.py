from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LogEntry(BaseModel):
    """日志条目模型"""
    timestamp: datetime
    level: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None

class LogQuery(BaseModel):
    """日志查询参数模型"""
    level: Optional[str] = Field(None, description="日志级别过滤")
    module: Optional[str] = Field(None, description="模块名称过滤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    message_contains: Optional[str] = Field(None, description="消息内容包含")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    order_desc: bool = Field(True, description="是否降序排列")

class LogStats(BaseModel):
    """日志统计信息"""
    total_count: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    today_count: int
    yesterday_count: int
    level_distribution: Dict[str, int]
    module_distribution: Dict[str, int]

class LogListResponse(BaseModel):
    """日志列表响应"""
    items: List[LogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int

class LogCreate(BaseModel):
    """创建日志请求模型"""
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    module: Optional[str] = Field(None, description="模块名称")
    function: Optional[str] = Field(None, description="函数名称")
    line: Optional[int] = Field(None, description="行号")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据") 