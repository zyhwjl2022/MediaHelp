from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from utils.scheduled_manager import scheduled_manager
from utils.scheduler import task_scheduler
from schemas.user import UserResponse as User
from api.deps import get_current_user
from utils.exceptions import APIException
from schemas.response import Response

router = APIRouter()

@router.get("/tasks", response_model=Response[List[Dict[str, Any]]])
async def get_tasks(current_user: User = Depends(get_current_user)):
    """获取所有定时任务"""
    tasks = scheduled_manager.get_tasks()
    # 为每个任务添加下次执行时间
    for task in tasks:
        next_run = scheduled_manager.get_next_run_time(task)
        task["next_run"] = next_run.isoformat() if next_run else None
    return Response(data=tasks)

@router.post("/tasks", response_model=Response[Dict[str, Any]])
async def create_task(
    task: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """创建定时任务"""
    # 验证任务处理器是否存在
    if task.get("task") not in task_scheduler._task_handlers:
        raise APIException(
            message="任务处理器不存在",
            detail=f"未找到任务处理器: {task.get('task')}"
        )
    
    # 添加任务
    if not scheduled_manager.add_task(task):
        raise APIException(message="创建任务失败")
    
    # 获取创建后的任务
    created_task = scheduled_manager.get_task_by_name(task["name"])
    if created_task:
        next_run = scheduled_manager.get_next_run_time(created_task)
        created_task["next_run"] = next_run.isoformat() if next_run else None
    
    return Response(data=created_task)

@router.put("/tasks/{task_name}", response_model=Response[Dict[str, Any]])
async def update_task(
    task_name: str,
    task: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """更新定时任务"""
    # 如果更新了任务类型，验证新的任务处理器是否存在
    if "task" in task and task["task"] not in task_scheduler._task_handlers:
        raise APIException(
            message="任务处理器不存在",
            detail=f"未找到任务处理器: {task['task']}"
        )
    
    # 更新任务
    if not scheduled_manager.update_task(task_name, task):
        raise APIException(message="更新任务失败")
    
    # 获取更新后的任务
    updated_task = scheduled_manager.get_task_by_name(task_name)
    if updated_task:
        next_run = scheduled_manager.get_next_run_time(updated_task)
        updated_task["next_run"] = next_run.isoformat() if next_run else None
    
    return Response(data=updated_task)

@router.delete("/tasks/{task_name}", response_model=Response)
async def delete_task(
    task_name: str,
    current_user: User = Depends(get_current_user)
):
    """删除定时任务"""
    if not scheduled_manager.delete_task(task_name):
        raise APIException(message="删除任务失败")
    return Response()

@router.post("/tasks/{task_name}/enable", response_model=Response[Dict[str, Any]])
async def enable_task(
    task_name: str,
    current_user: User = Depends(get_current_user)
):
    """启用定时任务"""
    if not scheduled_manager.enable_task(task_name):
        raise APIException(message="启用任务失败")
    
    # 获取更新后的任务
    task = scheduled_manager.get_task_by_name(task_name)
    if task:
        next_run = scheduled_manager.get_next_run_time(task)
        task["next_run"] = next_run.isoformat() if next_run else None
    
    return Response(data=task)

@router.post("/tasks/{task_name}/disable", response_model=Response[Dict[str, Any]])
async def disable_task(
    task_name: str,
    current_user: User = Depends(get_current_user)
):
    """禁用定时任务"""
    if not scheduled_manager.disable_task(task_name):
        raise APIException(message="禁用任务失败")
    
    # 获取更新后的任务
    task = scheduled_manager.get_task_by_name(task_name)
    if task:
        next_run = scheduled_manager.get_next_run_time(task)
        task["next_run"] = next_run.isoformat() if next_run else None
    
    return Response(data=task)

@router.get("/task-types", response_model=Response[List[str]])
async def get_task_types(current_user: User = Depends(get_current_user)):
    """获取所有可用的任务类型"""
    return Response(data=list(task_scheduler._task_handlers.keys())) 