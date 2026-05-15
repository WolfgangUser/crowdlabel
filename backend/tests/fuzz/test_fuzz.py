"""
Фаззинг-тестирование с использованием Hypothesis.
Тестирует устойчивость Pydantic-схем и эндпоинтов к случайным данным.
"""
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from pydantic import ValidationError

from app.schemas.schemas import (
    AnnotationCreate,
    AnnotationVerify,
    LoginRequest,
    RegisterRequest,
    TaskCreate,
    TaskUpdate,
    UserRoleUpdate,
)


# ─── Стратегии ────────────────────────────────────────────────────────────────

any_string = st.text(min_size=0, max_size=10_000)
any_int = st.integers(min_value=-2**31, max_value=2**31)
any_dict = st.dictionaries(st.text(max_size=50), st.text(max_size=200), max_size=10)
any_list = st.lists(st.text(max_size=100), max_size=20)


# ─── Schema Fuzzing ───────────────────────────────────────────────────────────

class TestRegisterRequestFuzz:
    @given(
        email=any_string,
        username=any_string,
        password=any_string,
        full_name=st.one_of(st.none(), any_string),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_never_crashes(self, email, username, password, full_name):
        """RegisterRequest никогда не должен вызывать необработанных исключений."""
        try:
            RegisterRequest(email=email, username=username, password=password, full_name=full_name)
        except ValidationError:
            pass  # Ожидаемо — схема должна отклонять невалидные данные
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(password=st.text(min_size=0, max_size=7))
    @settings(max_examples=100)
    def test_short_password_always_rejected(self, password):
        """Пароль < 8 символов всегда отклоняется."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@test.com", username="testuser", password=password
            )

    @given(username=st.text(alphabet="!@#$%^&*() ", min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_special_char_username_rejected(self, username):
        """Специальные символы в username всегда отклоняются."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@test.com", username=username, password="Valid123!"
            )


class TestAnnotationFuzz:
    @given(label=any_string, task_id=any_int, metadata=st.one_of(st.none(), any_dict))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_never_crashes(self, label, task_id, metadata):
        try:
            AnnotationCreate(task_id=task_id, label=label, metadata=metadata)
        except ValidationError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected: {type(e).__name__}: {e}")

    @given(label=st.just(""))
    @settings(max_examples=5)
    def test_empty_label_rejected(self, label):
        with pytest.raises(ValidationError):
            AnnotationCreate(task_id=1, label=label)

    @given(status=any_string)
    @settings(max_examples=100)
    def test_invalid_verify_status_rejected(self, status):
        try:
            v = AnnotationVerify(status=status)
            # Если создался — это должен быть валидный enum
            assert v.status in ("verified", "rejected", "pending")
            if v.status == "pending":
                pytest.fail("pending должен быть отклонён валидатором")
        except ValidationError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected: {type(e).__name__}: {e}")


class TestTaskCreateFuzz:
    @given(
        title=any_string,
        dataset_id=any_int,
        data=any_dict,
        annotations_required=any_int,
        reward_points=any_int,
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_never_crashes(self, title, dataset_id, data, annotations_required, reward_points):
        try:
            TaskCreate(
                title=title, dataset_id=dataset_id, data=data,
                annotations_required=annotations_required, reward_points=reward_points,
            )
        except ValidationError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected: {type(e).__name__}: {e}")

    @given(annotations_required=st.integers(max_value=0))
    @settings(max_examples=50)
    def test_zero_annotations_rejected(self, annotations_required):
        with pytest.raises(ValidationError):
            TaskCreate(
                title="T", dataset_id=1, data={}, annotations_required=annotations_required
            )

    @given(annotations_required=st.integers(min_value=11))
    @settings(max_examples=50)
    def test_too_many_annotations_rejected(self, annotations_required):
        with pytest.raises(ValidationError):
            TaskCreate(
                title="T", dataset_id=1, data={}, annotations_required=annotations_required
            )


class TestRoleFuzz:
    @given(role=any_string)
    @settings(max_examples=200)
    def test_invalid_role_rejected(self, role):
        """Любая строка кроме admin/manager/annotator должна быть отклонена."""
        if role in ("admin", "manager", "annotator"):
            return  # валидные значения — пропускаем
        with pytest.raises(ValidationError):
            UserRoleUpdate(role=role)


class TestLoginFuzz:
    @given(email=any_string, password=any_string)
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_schema_never_crashes(self, email, password):
        """LoginRequest схема никогда не падает с необработанным исключением."""
        try:
            LoginRequest(email=email, password=password)
        except ValidationError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected: {type(e).__name__}: {e}")


# ─── Граничные значения ───────────────────────────────────────────────────────

class TestBoundaryValues:
    def test_max_label_length(self):
        """Метка ровно 500 символов — допустима."""
        AnnotationCreate(task_id=1, label="x" * 500)

    def test_over_max_label_rejected(self):
        """Метка 501 символ — отклоняется."""
        with pytest.raises(ValidationError):
            AnnotationCreate(task_id=1, label="x" * 501)

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="", dataset_id=1, data={})

    def test_null_bytes_in_strings(self):
        """Null-байты в строках — отклоняются или обрабатываются."""
        try:
            RegisterRequest(email="test@test.com", username="user\x00name", password="Valid123!")
        except (ValidationError, ValueError):
            pass  # Ожидаемо
