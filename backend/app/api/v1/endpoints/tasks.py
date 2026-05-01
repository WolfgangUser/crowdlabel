"""CRUD эндпоинты для задач разметки."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, AnyUser, ManagerUser
from app.db.session import get_db
from app.models.user import TaskStatus, User
from app.schemas.schemas import Page, TaskCreate, TaskOut, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = ManagerUser):
    svc = TaskService(db)
    task = await svc.create(data, current_user.id)
    await db.commit()
    task.annotation_count = 0
    return task


@router.get("", response_model=Page)
async def list_tasks(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    dataset_id: int | None = None, db: AsyncSession = Depends(get_db), _: User = AnyUser,
):
    svc = TaskService(db)
    tasks, total = await svc.list_tasks((page-1)*size, size, status_filter, dataset_id)
    items = [TaskOut.model_validate(t).model_dump() for t in tasks]
    return Page(items=items, total=total, page=page, size=size, pages=(total+size-1)//size)


@router.get("/available", response_model=Page)
async def available_tasks(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), current_user: User = AnyUser,
):
    svc = TaskService(db)
    tasks, total = await svc.available_for_user(current_user.id, (page-1)*size, size)
    items = [TaskOut.model_validate(t).model_dump() for t in tasks]
    return Page(items=items, total=total, page=page, size=size, pages=(total+size-1)//size)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), _: User = AnyUser):
    task = await TaskService(db).get_by_id(task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    task.annotation_count = len(task.annotations)
    return task


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, data: TaskUpdate, db: AsyncSession = Depends(get_db), _: User = ManagerUser):
    task = await TaskService(db).update(task_id, data)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    await db.commit()
    task.annotation_count = len(task.annotations)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), _: User = AdminUser):
    if not await TaskService(db).delete(task_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
