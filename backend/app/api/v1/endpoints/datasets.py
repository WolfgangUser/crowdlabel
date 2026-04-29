"""Эндпоинты для датасетов."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AnyUser, ManagerUser
from app.db.session import get_db
from app.models.user import Dataset, User
from app.schemas.schemas import DatasetCreate, DatasetOut, Page

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=Page)
async def list_datasets(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = AnyUser,
):
    count = await db.execute(select(func.count(Dataset.id)))
    total = count.scalar()
    result = await db.execute(
        select(Dataset).order_by(Dataset.created_at.desc())
        .offset((page - 1) * size).limit(size)
    )
    datasets = list(result.scalars())
    items = [DatasetOut.model_validate(ds).model_dump() for ds in datasets]
    return Page(items=items, total=total, page=page, size=size, pages=(total + size - 1) // size)


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = ManagerUser,
):
    ds = Dataset(
        name=data.name,
        description=data.description,
        task_type=data.task_type,
        labels=data.labels,
        creator_id=current_user.id,
    )
    db.add(ds)
    await db.flush()
    await db.commit()
    return ds


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = AnyUser,
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Датасет не найден")
    return ds
