"""Административное управление пользователями."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser
from app.db.session import get_db
from app.models.user import User
from app.schemas.schemas import Page, UserOut, UserRoleUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = AdminUser,
):
    from app.schemas.schemas import UserOut as _UO
    svc = UserService(db)
    users, total = await svc.list_users((page - 1) * size, size)
    items = [_UO.model_validate(u).model_dump() for u in users]
    return Page(items=items, total=total, page=page, size=size, pages=(total + size - 1) // size)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = AdminUser):
    user = await UserService(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.put("/{user_id}/role", response_model=UserOut)
async def update_role(
    user_id: int,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = AdminUser,
):
    user = await UserService(db).update_role(user_id, data.role)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = AdminUser,
):
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя деактивировать себя")
    user = await UserService(db).deactivate(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
