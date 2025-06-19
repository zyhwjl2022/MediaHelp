from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from utils.emby_manager import EmbyManager
from schemas.emby import (
    SyncJobCreate,
    SyncJobResponse,
    SyncJobStatus,
    SyncJobItems,
    EmbyItemResponse
)

router = APIRouter(prefix="/emby", tags=["emby"])
emby_manager = EmbyManager()

@router.get("/items/{user_id}", response_model=EmbyItemResponse)
async def get_items(
    user_id: str,
    parent_id: Optional[str] = None,
    item_types: Optional[List[str]] = None,
    recursive: bool = False,
    sort_by: Optional[List[str]] = None,
    sort_order: Optional[str] = None,
    filters: Optional[List[str]] = None,
    limit: Optional[int] = None,
    fields: Optional[List[str]] = None
):
    """获取媒体项目列表"""
    try:
        items = await emby_manager.get_items(
            user_id=user_id,
            parent_id=parent_id,
            include_item_types=item_types,
            recursive=recursive,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
            limit=limit,
            fields=fields
        )
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{user_id}/{item_id}", response_model=EmbyItemResponse)
async def get_item_details(user_id: str, item_id: str):
    """获取单个媒体项目的详细信息"""
    try:
        item = await emby_manager.get_item_details(user_id, item_id)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{user_id}/resumable", response_model=EmbyItemResponse)
async def get_resumable_items(user_id: str, limit: int = 20):
    """获取可继续播放的项目"""
    try:
        items = await emby_manager.get_resumable_items(user_id, limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/jobs", response_model=List[SyncJobResponse])
async def get_sync_jobs(target_id: Optional[str] = None):
    """获取同步任务列表"""
    try:
        jobs = await emby_manager.get_sync_jobs(target_id)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/jobs", response_model=SyncJobResponse)
async def create_sync_job(job: SyncJobCreate):
    """创建同步任务"""
    try:
        created_job = await emby_manager.create_sync_job(
            target_id=job.target_id,
            item_ids=job.item_ids,
            quality=job.quality,
            parent_id=job.parent_id,
            unwatched_only=job.unwatched_only,
            sync_new_content=job.sync_new_content,
            item_limit=job.item_limit
        )
        return created_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sync/jobs/{job_id}")
async def delete_sync_job(job_id: str):
    """删除同步任务"""
    try:
        await emby_manager.delete_sync_job(job_id)
        return {"message": "同步任务已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/jobs/{job_id}/status", response_model=SyncJobStatus)
async def get_sync_job_status(job_id: str):
    """获取同步任务状态"""
    try:
        status = await emby_manager.get_sync_job_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/jobs/{job_id}/items", response_model=SyncJobItems)
async def get_sync_job_items(job_id: str):
    """获取同步任务中的项目列表"""
    try:
        items = await emby_manager.get_sync_job_items(job_id)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/views", response_model=List[dict])
async def get_user_views(user_id: str):
    """获取用户的媒体库视图"""
    try:
        views = await emby_manager.get_user_views(user_id)
        return views
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_system_info():
    """获取Emby系统信息"""
    try:
        info = await emby_manager.get_system_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_items(
    search_term: str,
    include_item_types: Optional[List[str]] = None,
    limit: int = 10,
    recursive: bool = True
):
    """搜索媒体项目"""
    try:
        results = await emby_manager.search_items(
            search_term=search_term,
            include_item_types=include_item_types,
            limit=limit,
            recursive=recursive
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items/{item_id}/refresh")
async def refresh_item(
    item_id: str,
    recursive: bool = True,
    metadata_refresh_mode: str = "FullRefresh",
    image_refresh_mode: str = "FullRefresh",
    replace_all_metadata: bool = False,
    replace_all_images: bool = False
):
    """刷新媒体项目元数据"""
    try:
        success = await emby_manager.refresh_item(
            item_id=item_id,
            recursive=recursive,
            metadata_refresh_mode=metadata_refresh_mode,
            image_refresh_mode=image_refresh_mode,
            replace_all_metadata=replace_all_metadata,
            replace_all_images=replace_all_images
        )
        if success:
            return {"message": "媒体项目刷新成功"}
        else:
            raise HTTPException(status_code=500, detail="媒体项目刷新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movies/{user_id}")
async def get_all_movies(user_id: str):
    """获取所有电影"""
    try:
        movies = await emby_manager.get_all_movies(user_id)
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/episodes/{user_id}")
async def get_all_episodes(user_id: str):
    """获取所有剧集"""
    try:
        episodes = await emby_manager.get_all_episodes(user_id)
        return episodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))