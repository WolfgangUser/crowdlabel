"""
Сервис аннотаций — создание, верификация, статистика.
"""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Annotation, AnnotationStatus, Task, TaskStatus
from app.schemas.schemas import AnnotationCreate, AnnotationVerify


class AnnotationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit(self, data: AnnotationCreate, annotator_id: int) -> Annotation:
        # Проверяем, что задача активна
        task = await self.db.get(Task, data.task_id)
        if not task or task.status != TaskStatus.ACTIVE:
            raise ValueError("Задача недоступна для разметки")

        annotation = Annotation(
            task_id=data.task_id,
            annotator_id=annotator_id,
            label=data.label,
            metadata_=data.metadata_,
        )
        self.db.add(annotation)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Вы уже разметили эту задачу")

        # Автоматически завершаем задачу при достижении порога
        count_q = await self.db.execute(
            select(func.count(Annotation.id)).where(
                Annotation.task_id == data.task_id,
                Annotation.status.in_([AnnotationStatus.PENDING, AnnotationStatus.VERIFIED]),
            )
        )
        count = count_q.scalar()
        if count >= task.annotations_required:
            task.status = TaskStatus.COMPLETED
        await self.db.flush()
        return annotation

    async def get_for_task(self, task_id: int) -> list[Annotation]:
        result = await self.db.execute(
            select(Annotation).where(Annotation.task_id == task_id)
        )
        return list(result.scalars())

    async def get_by_id(self, annotation_id: int) -> Annotation | None:
        return await self.db.get(Annotation, annotation_id)

    async def verify(
        self, annotation_id: int, data: AnnotationVerify, verifier_id: int
    ) -> Annotation | None:
        annotation = await self.get_by_id(annotation_id)
        if not annotation:
            return None
        annotation.status = data.status
        annotation.verified_by = verifier_id
        annotation.comment = data.comment
        await self.db.flush()
        return annotation

    async def my_annotations(self, user_id: int) -> list[Annotation]:
        result = await self.db.execute(
            select(Annotation)
            .where(Annotation.annotator_id == user_id)
            .order_by(Annotation.created_at.desc())
        )
        return list(result.scalars())
