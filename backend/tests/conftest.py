"""Фикстуры pytest для интеграционных тестов."""
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.user import Base, Dataset, TaskType, User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db):
    u = User(email="admin@crowdlabel.io", username="admin",
             hashed_password=hash_password("Admin123!"), role=UserRole.ADMIN)
    db.add(u); await db.flush(); return u


@pytest_asyncio.fixture
async def manager_user(db):
    u = User(email="manager@crowdlabel.io", username="manager",
             hashed_password=hash_password("Manager123!"), role=UserRole.MANAGER)
    db.add(u); await db.flush(); return u


@pytest_asyncio.fixture
async def annotator_user(db):
    u = User(email="annotator@crowdlabel.io", username="annotator",
             hashed_password=hash_password("Annotator123!"), role=UserRole.ANNOTATOR)
    db.add(u); await db.flush(); return u


async def _login(client, email, password):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    return await _login(client, "admin@crowdlabel.io", "Admin123!")


@pytest_asyncio.fixture
async def manager_token(client, manager_user):
    return await _login(client, "manager@crowdlabel.io", "Manager123!")


@pytest_asyncio.fixture
async def annotator_token(client, annotator_user):
    return await _login(client, "annotator@crowdlabel.io", "Annotator123!")


@pytest_asyncio.fixture
async def annotator_id(annotator_user):
    return annotator_user.id


@pytest_asyncio.fixture
async def dataset_id(db, manager_user):
    ds = Dataset(name="Test DS", task_type=TaskType.TEXT_CLASSIFICATION,
                 labels=["a", "b"], creator_id=manager_user.id)
    db.add(ds); await db.flush(); return ds.id
