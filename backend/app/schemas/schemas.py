"""
Pydantic v2 схемы для запросов и ответов.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import AnnotationStatus, TaskStatus, TaskType, UserRole


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=100)
    full_name: str | None = Field(None, max_length=200)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    username: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: UserRole


# ─── Dataset ──────────────────────────────────────────────────────────────────

class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    task_type: TaskType
    labels: list[str] = Field(min_length=2)


class DatasetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    task_type: TaskType
    labels: list[str]
    creator_id: int
    created_at: datetime


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    dataset_id: int
    data: dict[str, Any]
    annotations_required: int = Field(default=3, ge=1, le=10)
    reward_points: int = Field(default=10, ge=1, le=1000)


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    status: TaskStatus | None = None
    annotations_required: int | None = Field(None, ge=1, le=10)


class TaskOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: str | None
    dataset_id: int
    creator_id: int
    status: TaskStatus
    data: dict[str, Any]
    annotations_required: int
    reward_points: int
    created_at: datetime
    updated_at: datetime
    annotation_count: int = 0


# ─── Annotation ───────────────────────────────────────────────────────────────

class AnnotationCreate(BaseModel):
    task_id: int
    label: str = Field(min_length=1, max_length=500)
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")

    model_config = {"populate_by_name": True}


class AnnotationVerify(BaseModel):
    status: AnnotationStatus = Field(
        ..., description="verified или rejected"
    )
    comment: str | None = Field(None, max_length=1000)

    @field_validator("status")
    @classmethod
    def must_be_decision(cls, v: AnnotationStatus) -> AnnotationStatus:
        if v == AnnotationStatus.PENDING:
            raise ValueError("Статус должен быть verified или rejected")
        return v


class AnnotationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    task_id: int
    annotator_id: int
    label: str
    metadata_: dict | None = None
    status: AnnotationStatus
    verified_by: int | None
    comment: str | None
    created_at: datetime


# ─── Pagination ───────────────────────────────────────────────────────────────

class Page(BaseModel):
    model_config = {"from_attributes": True}
    items: list[Any]
    total: int
    page: int
    size: int
    pages: int
