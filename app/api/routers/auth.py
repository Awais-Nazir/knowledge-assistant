from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.register(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.login(db, data)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.refresh(db, data)


@router.post(
    "/logout",
    response_model=SuccessResponse,
)
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout(db, data.refresh_token)
    return SuccessResponse(message="Logged out successfully")


@router.post(
    "/logout-all",
    response_model=SuccessResponse,
)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await auth_service.logout_all(db, str(current_user.id))
    return SuccessResponse(message="Logged out from all devices successfully")


# @router.post(
#     "/logout",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# async def logout(
#     data: RefreshRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     await auth_service.logout(db, data.refresh_token)


# @router.post(
#     "/logout-all",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# async def logout_all(
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     await auth_service.logout_all(db, str(current_user.id))


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)
