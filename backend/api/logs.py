from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from api.deps import get_current_user
from models.user import User
from schemas.log import LogQuery, LogStats, LogListResponse
from schemas.response import Response
from utils.logger_service import logger_service

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/list", response_model=Response[LogListResponse])
async def get_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    module: Optional[str] = Query(None, description="模块名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    message_contains: Optional[str] = Query(None, description="消息内容包含"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_desc: bool = Query(True, description="是否降序排列"),
    current_user: User = Depends(get_current_user)
):
    """获取日志列表"""
    query = LogQuery(
        level=level,
        module=module,
        start_time=start_time,
        end_time=end_time,
        message_contains=message_contains,
        page=page,
        page_size=page_size,
        order_desc=order_desc
    )
    
    data = await logger_service.read_logs(query)
    return Response(data=data)

@router.get("/stats", response_model=Response[LogStats])
async def get_log_stats(
    current_user: User = Depends(get_current_user)
    
):
    """获取日志统计信息"""
    return await logger_service.get_stats()

@router.get("/modules", response_model=Response[List[str]])
async def get_modules(
    current_user: User = Depends(get_current_user)
    
):
    """获取所有模块名称"""
    return Response(data=await logger_service.get_modules())

@router.get("/levels", response_model=Response[List[str]])
async def get_levels(
    current_user: User = Depends(get_current_user)
    
):
    """获取所有日志级别"""
    return Response(data=await logger_service.get_levels())

@router.post("/clear")
async def clear_logs(
    current_user: User = Depends(get_current_user)
    
):
    """清空日志文件"""
    cleared = await logger_service.clear_logs()
    return Response(data={"message": "日志已清空" if cleared else "无日志需要清空", "cleared": cleared})

@router.post("/test")
async def test_log(
    current_user: User = Depends(get_current_user),
    message: str = Query(..., description="测试日志消息"),
    level: str = Query("INFO", description="日志级别")
):
    """测试日志记录"""
    await logger_service.log(level, message, extra_data={"test": True})
    return Response(data={"message": "测试日志记录成功"}) 