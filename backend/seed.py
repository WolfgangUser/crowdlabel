"""
Заполнение базы данных тестовыми данными.
12-factor Factor XII: задача администрирования — отдельный процесс.

Запуск: python seed.py
"""
import asyncio
import sys

from loguru import logger
from sqlalchemy import text

sys.path.insert(0, ".")

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.user import (
    Annotation, AnnotationStatus, Base, Dataset,
    Task, TaskStatus, TaskType, User, UserRole,
)


async def drop_and_create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Схема БД создана")


async def seed():
    await drop_and_create()

    async with AsyncSessionLocal() as db:
        # ── Пользователи ──────────────────────────────────────────────────
        users_data = [
            dict(email="admin@crowdlabel.io", username="admin", full_name="Администратор Системы",
                 role=UserRole.ADMIN, password="Admin123!"),
            dict(email="manager@crowdlabel.io", username="manager", full_name="Менеджер Проектов",
                 role=UserRole.MANAGER, password="Manager123!"),
            dict(email="manager2@crowdlabel.io", username="manager2", full_name="Второй Менеджер",
                 role=UserRole.MANAGER, password="Manager123!"),
            dict(email="annotator@crowdlabel.io", username="annotator", full_name="Аннотатор Один",
                 role=UserRole.ANNOTATOR, password="Annotator123!"),
            dict(email="ann2@crowdlabel.io", username="ann2", full_name="Аннотатор Два",
                 role=UserRole.ANNOTATOR, password="Annotator123!"),
            dict(email="ann3@crowdlabel.io", username="ann3", full_name="Аннотатор Три",
                 role=UserRole.ANNOTATOR, password="Annotator123!"),
        ]
        users = []
        for ud in users_data:
            u = User(
                email=ud["email"], username=ud["username"],
                full_name=ud["full_name"], role=ud["role"],
                hashed_password=hash_password(ud["password"]),
            )
            db.add(u)
            users.append(u)
        await db.flush()
        admin, manager, manager2, ann1, ann2, ann3 = users
        logger.info("✅ Пользователи созданы: {}", len(users))

        # ── Датасеты ──────────────────────────────────────────────────────
        ds1 = Dataset(
            name="Классификация изображений котов и собак",
            description="Популярный датасет для бинарной классификации",
            task_type=TaskType.IMAGE_CLASSIFICATION,
            labels=["cat", "dog"],
            creator_id=manager.id,
        )
        ds2 = Dataset(
            name="Сентимент-анализ отзывов",
            description="Отзывы о товарах с маркировкой тональности",
            task_type=TaskType.SENTIMENT,
            labels=["positive", "negative", "neutral"],
            creator_id=manager.id,
        )
        ds3 = Dataset(
            name="NER — именованные сущности в новостях",
            description="Выделение персон, организаций, мест",
            task_type=TaskType.NER,
            labels=["PER", "ORG", "LOC", "MISC"],
            creator_id=manager2.id,
        )
        db.add_all([ds1, ds2, ds3])
        await db.flush()
        logger.info("✅ Датасеты созданы: 3")

        # ── Задачи разметки ───────────────────────────────────────────────
        tasks_data = [
            Task(title="Кот или собака #001", dataset_id=ds1.id, creator_id=manager.id,
                 status=TaskStatus.ACTIVE,
                 data={"url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", "filename": "pet001.jpg"},
                 annotations_required=3, reward_points=5),
            Task(title="Кот или собака #002", dataset_id=ds1.id, creator_id=manager.id,
                 status=TaskStatus.ACTIVE,
                 data={"url": "https://images.unsplash.com/photo-1587300003388-59208cc962cb", "filename": "pet002.jpg"},
                 annotations_required=3, reward_points=5),
            Task(title="Кот или собака #003", dataset_id=ds1.id, creator_id=manager.id,
                 status=TaskStatus.COMPLETED,
                 data={"url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1", "filename": "pet003.jpg"},
                 annotations_required=3, reward_points=5),
            Task(title="Отзыв: «Отличный товар, очень доволен!»", dataset_id=ds2.id, creator_id=manager.id,
                 status=TaskStatus.ACTIVE,
                 data={"text": "Отличный товар, очень доволен покупкой! Рекомендую всем."},
                 annotations_required=2, reward_points=10),
            Task(title="Отзыв: «Полный провал, вернул через день»", dataset_id=ds2.id, creator_id=manager.id,
                 status=TaskStatus.ACTIVE,
                 data={"text": "Полный провал. Качество ужасное, вернул через день."},
                 annotations_required=2, reward_points=10),
            Task(title="Отзыв: «Обычный товар, ничего особенного»", dataset_id=ds2.id, creator_id=manager.id,
                 status=TaskStatus.DRAFT,
                 data={"text": "Обычный товар. Ничего особенного, просто выполняет свою функцию."},
                 annotations_required=2, reward_points=10),
            Task(title="NER: «Путин встретился с Меркель в Берлине»", dataset_id=ds3.id, creator_id=manager2.id,
                 status=TaskStatus.ACTIVE,
                 data={"text": "Путин встретился с Меркель в Берлине для обсуждения вопросов безопасности.",
                       "tokens": ["Путин", "встретился", "с", "Меркель", "в", "Берлине"]},
                 annotations_required=3, reward_points=20),
        ]
        task_objs = []
        for t in tasks_data:
            db.add(t)
            task_objs.append(t)
        await db.flush()
        logger.info("✅ Задачи созданы: {}", len(task_objs))

        # ── Аннотации ─────────────────────────────────────────────────────
        t1, t2, t3, t4, t5, t6, t7 = task_objs
        annotations_data = [
            # Task 1 — активная
            Annotation(task_id=t1.id, annotator_id=ann1.id, label="cat", status=AnnotationStatus.VERIFIED, verified_by=manager.id),
            Annotation(task_id=t1.id, annotator_id=ann2.id, label="cat", status=AnnotationStatus.VERIFIED, verified_by=manager.id),
            # Task 3 — завершённая
            Annotation(task_id=t3.id, annotator_id=ann1.id, label="dog", status=AnnotationStatus.VERIFIED, verified_by=manager.id),
            Annotation(task_id=t3.id, annotator_id=ann2.id, label="dog", status=AnnotationStatus.VERIFIED, verified_by=manager.id),
            Annotation(task_id=t3.id, annotator_id=ann3.id, label="cat", status=AnnotationStatus.REJECTED, verified_by=manager.id, comment="Неправильная метка"),
            # Task 4 — сентимент
            Annotation(task_id=t4.id, annotator_id=ann1.id, label="positive", status=AnnotationStatus.PENDING),
            Annotation(task_id=t4.id, annotator_id=ann2.id, label="positive", status=AnnotationStatus.PENDING),
            # Task 7 — NER
            Annotation(task_id=t7.id, annotator_id=ann1.id, label='{"Путин": "PER", "Меркель": "PER", "Берлине": "LOC"}', status=AnnotationStatus.PENDING),
        ]
        for a in annotations_data:
            db.add(a)
        await db.flush()
        logger.info("✅ Аннотации созданы: {}", len(annotations_data))

        await db.commit()

    logger.success("🎉 База данных заполнена тестовыми данными!")
    logger.info("  Admin:     admin@crowdlabel.io / Admin123!")
    logger.info("  Manager:   manager@crowdlabel.io / Manager123!")
    logger.info("  Annotator: annotator@crowdlabel.io / Annotator123!")


if __name__ == "__main__":
    asyncio.run(seed())
