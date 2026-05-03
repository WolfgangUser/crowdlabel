"""Эндпоинты для аннотаций."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AnyUser, ManagerUser
from app.db.session import get_db
from app.models.user import User
from app.schemas.schemas import AnnotationCreate, AnnotationOut, AnnotationVerify
from app.services.annotation_service import AnnotationService

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.post("", response_model=AnnotationOut, status_code=status.HTTP_201_CREATED)
async def submit_annotation(
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyUser,
):
    svc = AnnotationService(db)
    try:
        annotation = await svc.submit(data, current_user.id)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    await db.commit()
    return annotation


@router.get("/my", response_model=list[AnnotationOut])
async def my_annotations(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyUser,
):
    svc = AnnotationService(db)
    return await svc.my_annotations(current_user.id)


@router.get("/task/{task_id}", response_model=list[AnnotationOut])
async def task_annotations(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = ManagerUser,
):
    svc = AnnotationService(db)
    return await svc.get_for_task(task_id)


@router.put("/{annotation_id}/verify", response_model=AnnotationOut)
async def verify_annotation(
    annotation_id: int,
    data: AnnotationVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = ManagerUser,
):
    svc = AnnotationService(db)
    annotation = await svc.verify(annotation_id, data, current_user.id)
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Аннотация не найдена")
    await db.commit()
    return annotation
