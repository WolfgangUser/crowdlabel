"""
Тесты аутентификации, авторизации и ролевой модели.
Валидация некорректных данных (требование п.4).
"""
import pytest
from httpx import AsyncClient


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestRegistration:
    async def test_register_success(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "Valid123!",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["role"] == "annotator"
        assert data["email"] == "newuser@test.com"

    async def test_register_duplicate_email(self, client: AsyncClient, annotator_token):
        r = await client.post("/api/v1/auth/register", json={
            "email": "annotator@crowdlabel.io",
            "username": "another",
            "password": "Valid123!",
        })
        assert r.status_code == 409

    @pytest.mark.parametrize("password,expected_msg", [
        ("short", "минимум"),
        ("alllowercase1", "заглавную"),

        ("NoDigitsHere!", "цифру"),
    ])
    async def test_weak_password_rejected(self, client: AsyncClient, password, expected_msg):
        r = await client.post("/api/v1/auth/register", json={
            "email": "weak@test.com", "username": "weakuser", "password": password,
        })
        assert r.status_code == 422

    async def test_invalid_email_format(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email", "username": "usr", "password": "Valid123!",
        })
        assert r.status_code == 422

    async def test_username_special_chars_rejected(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "x@test.com", "username": "user name!", "password": "Valid123!",
        })
        assert r.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, annotator_user):
        r = await client.post("/api/v1/auth/login", json={
            "email": "annotator@crowdlabel.io", "password": "Annotator123!",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_wrong_password(self, client: AsyncClient, annotator_user):
        r = await client.post("/api/v1/auth/login", json={
            "email": "annotator@crowdlabel.io", "password": "wrongpassword",
        })
        assert r.status_code == 401

    async def test_nonexistent_user(self, client: AsyncClient, annotator_user):
        r = await client.post("/api/v1/auth/login", json={
            "email": "ghost@test.com", "password": "Valid123!",
        })
        assert r.status_code == 401

    async def test_no_token_unauthorized(self, client: AsyncClient, annotator_user):
        r = await client.get("/api/v1/tasks")
        assert r.status_code == 401

    async def test_invalid_token(self, client: AsyncClient):
        r = await client.get(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert r.status_code == 401


# ─── RBAC Tests ───────────────────────────────────────────────────────────────

class TestRoleModel:
    """Валидация ролевой модели — попытки нарушить ограничения."""

    async def test_annotator_cannot_create_task(self, client: AsyncClient, annotator_token):
        r = await client.post(
            "/api/v1/tasks",
            json={"title": "Hack", "dataset_id": 1, "data": {}, "annotations_required": 1},
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 403

    async def test_annotator_cannot_list_users(self, client: AsyncClient, annotator_token):
        r = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 403

    async def test_annotator_cannot_update_role(self, client: AsyncClient, annotator_token):
        r = await client.put(
            "/api/v1/users/1/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 403

    async def test_annotator_cannot_delete_task(self, client: AsyncClient, annotator_token):
        r = await client.delete(
            "/api/v1/tasks/1",
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 403

    async def test_manager_cannot_delete_task(self, client: AsyncClient, manager_token):
        r = await client.delete(
            "/api/v1/tasks/1",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403

    async def test_manager_cannot_list_users(self, client: AsyncClient, manager_token):
        r = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403

    async def test_manager_can_create_task(self, client: AsyncClient, manager_token, dataset_id):
        r = await client.post(
            "/api/v1/tasks",
            json={"title": "Легитимная задача", "dataset_id": dataset_id,
                  "data": {"text": "test"}, "annotations_required": 1},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 201

    async def test_admin_can_list_users(self, client: AsyncClient, admin_token):
        r = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200

    async def test_admin_can_update_role(self, client: AsyncClient, admin_token, annotator_id):
        r = await client.put(
            f"/api/v1/users/{annotator_id}/role",
            json={"role": "manager"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "manager"

    async def test_invalid_role_value(self, client: AsyncClient, admin_token, annotator_id):
        r = await client.put(
            f"/api/v1/users/{annotator_id}/role",
            json={"role": "superuser"},  # несуществующая роль
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422

    async def test_annotator_cannot_verify_annotation(self, client: AsyncClient, annotator_token):
        r = await client.put(
            "/api/v1/annotations/1/verify",
            json={"status": "verified"},
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 403

    async def test_annotation_verify_pending_status_rejected(self, client: AsyncClient, manager_token):
        """Верификация со статусом 'pending' — ошибка валидации."""
        r = await client.put(
            "/api/v1/annotations/1/verify",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 422
