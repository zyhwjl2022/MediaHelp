from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user as user_crud
from schemas.auth import Token, LoginRequest
from schemas.user import UserCreate, UserResponse
from utils.auth import create_access_token
from crud.database import get_db_session
from crud.config import settings
from models.user import User
from api.deps import get_current_user
from schemas.response import Response

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=Response)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户登录
    
    请求体示例:
    ```json
    {
        "username": "admin",
        "password": "admin"
    }
    ```
    """
    # 验证用户
    user = await user_crud.authenticate(
        db, username=login_data.username, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )

    # 创建访问令牌
    access_token_expires = timedelta(
        minutes=settings.security_config["access_token_expire_minutes"]
    )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Response(data=Token(access_token=access_token))

@router.post("/users", response_model=Response, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    创建新用户（需要登录权限）
    
    请求体示例:
    ```json
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "is_active": true
    }
    ```
    """
    # 检查用户名是否已存在
    db_user = await user_crud.get_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    db_user = await user_crud.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    user = await user_crud.create(db, obj_in=user_in)
    return Response(data=user)

@router.get("/user/info", response_model=Response[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    
    返回示例:
    ```json
    {
        "code": 200,
        "message": "操作成功",
        "data": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "is_active": true,
            "created_at": "2024-03-20T10:00:00",
            "updated_at": "2024-03-20T10:00:00"
        }
    }
    ```
    """
    return Response(data=UserResponse.model_validate(current_user))

