"""
Сервис для работы с пользователями.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.schemas import RegisterRequest


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, data: RegisterRequest) -> User:
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.ANNOTATOR,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def list_users(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        from sqlalchemy import func
        count_q = await self.db.execute(select(func.count(User.id)))
        total = count_q.scalar()
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars()), total

    async def update_role(self, user_id: int, role: UserRole) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.role = role
        await self.db.flush()
        return user

    async def deactivate(self, user_id: int) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.is_active = False
        await self.db.flush()
        return user
