from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user as user_crud
from crud.database import get_db_session
from models.user import User
from utils.auth import decode_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    获取当前登录用户
    
    用法:
    ```python
    @router.get("/some-protected-route")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"message": f"Hello {current_user.username}"}
    ```
    """
    payload = await decode_token(credentials.credentials)
    username: str = payload.get("sub")
    
    user = await user_crud.get_by_username(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户（已登录且已激活）
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user 