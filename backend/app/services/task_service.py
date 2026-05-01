"""
Сервис для работы с задачами разметки.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Annotation, Task, TaskStatus
from app.schemas.schemas import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: TaskCreate, creator_id: int) -> Task:
        task = Task(
            title=data.title,
            description=data.description,
            dataset_id=data.dataset_id,
            creator_id=creator_id,
            data=data.data,
            annotations_required=data.annotations_required,
            reward_points=data.reward_points,
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_by_id(self, task_id: int) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.annotations))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 20,
        status: TaskStatus | None = None,
        dataset_id: int | None = None,
    ) -> tuple[list[Task], int]:
        q = select(Task)
        if status:
            q = q.where(Task.status == status)
        if dataset_id:
            q = q.where(Task.dataset_id == dataset_id)

        count = await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count.scalar()

        result = await self.db.execute(
            q.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        )
        tasks = list(result.scalars())

        # Добавляем счётчик аннотаций
        for task in tasks:
            cnt = await self.db.execute(
                select(func.count(Annotation.id)).where(Annotation.task_id == task.id)
            )
            task.annotation_count = cnt.scalar()

        return tasks, total

    async def update(self, task_id: int, data: TaskUpdate) -> Task | None:
        task = await self.get_by_id(task_id)
        if not task:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(task, field, value)
        await self.db.flush()
        return task

    async def delete(self, task_id: int) -> bool:
        task = await self.get_by_id(task_id)
        if not task:
            return False
        self.db.delete(task)
        await self.db.flush()
        return True

    async def available_for_user(self, user_id: int, skip: int, limit: int) -> tuple[list[Task], int]:
        """Задачи без аннотации от данного пользователя."""
        subq = (
            select(Annotation.task_id)
            .where(Annotation.annotator_id == user_id)
            .scalar_subquery()
        )
        q = (
            select(Task)
            .where(Task.status == TaskStatus.ACTIVE)
            .where(Task.id.not_in(subq))
        )
        count = await self.db.execute(select(func.count()).select_from(q.subquery()))
        total = count.scalar()
        result = await self.db.execute(q.offset(skip).limit(limit))
        tasks = list(result.scalars())
        for task in tasks:
            cnt = await self.db.execute(
                select(func.count(Annotation.id)).where(Annotation.task_id == task.id)
            )
            task.annotation_count = cnt.scalar()
        return tasks, total
