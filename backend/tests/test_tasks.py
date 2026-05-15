"""
Интеграционные тесты CRUD задач разметки.
"""
import pytest
from httpx import AsyncClient


class TestTasksCRUD:

    async def test_create_task_as_manager(self, client: AsyncClient, manager_token, dataset_id):
        r = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Новая задача классификации",
                "description": "Определите объект на изображении",
                "dataset_id": dataset_id,
                "data": {"url": "https://example.com/img.jpg"},
                "annotations_required": 3,
                "reward_points": 15,
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Новая задача классификации"
        assert data["status"] == "draft"
        assert data["annotations_required"] == 3
        return data["id"]

    async def test_get_task(self, client: AsyncClient, manager_token, dataset_id):
        # Создаём задачу
        cr = await client.post(
            "/api/v1/tasks",
            json={"title": "Task for GET", "dataset_id": dataset_id,
                  "data": {"text": "test"}, "annotations_required": 1},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        task_id = cr.json()["id"]

        r = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["id"] == task_id

    async def test_get_nonexistent_task(self, client: AsyncClient, manager_token):
        r = await client.get(
            "/api/v1/tasks/99999",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 404

    async def test_update_task_status(self, client: AsyncClient, manager_token, dataset_id):
        cr = await client.post(
            "/api/v1/tasks",
            json={"title": "Task to activate", "dataset_id": dataset_id,
                  "data": {}, "annotations_required": 1},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        task_id = cr.json()["id"]

        r = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    async def test_list_tasks_pagination(self, client: AsyncClient, annotator_token):
        r = await client.get(
            "/api/v1/tasks?page=1&size=5",
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "pages" in data
        assert len(data["items"]) <= 5

    async def test_list_tasks_filter_by_status(self, client: AsyncClient, manager_token):
        r = await client.get(
            "/api/v1/tasks?status=draft",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        for task in r.json()["items"]:
            assert task["status"] == "draft"

    async def test_invalid_page_size_rejected(self, client: AsyncClient, annotator_token):
        r = await client.get(
            "/api/v1/tasks?size=999",
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 422

    async def test_invalid_status_filter_rejected(self, client: AsyncClient, manager_token):
        r = await client.get(
            "/api/v1/tasks?status=invalid_status",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 422


class TestAnnotationsCRUD:

    async def test_submit_annotation(self, client: AsyncClient, annotator_token, manager_token, dataset_id):
        # Создаём активную задачу
        cr = await client.post(
            "/api/v1/tasks",
            json={"title": "Annotation test task", "dataset_id": dataset_id,
                  "data": {"text": "Это позитивный отзыв!"}, "annotations_required": 2},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        task_id = cr.json()["id"]
        # Активируем
        await client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )

        r = await client.post(
            "/api/v1/annotations",
            json={"task_id": task_id, "label": "positive"},
            headers={"Authorization": f"Bearer {annotator_token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["label"] == "positive"
        assert data["status"] == "pending"

    async def test_duplicate_annotation_rejected(self, client: AsyncClient, annotator_token, manager_token, dataset_id):
        cr = await client.post(
            "/api/v1/tasks",
            json={"title": "Dup test", "dataset_id": dataset_id,
                  "data": {"text": "test"}, "annotations_required": 3},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        task_id = cr.json()["id"]
        await client.put(f"/api/v1/tasks/{task_id}", json={"status": "active"},
                         headers={"Authorization": f"Bearer {manager_token}"})

        await client.post("/api/v1/annotations",
                          json={"task_id": task_id, "label": "cat"},
                          headers={"Authorization": f"Bearer {annotator_token}"})
        # Повторная аннотация
        r = await client.post("/api/v1/annotations",
                              json={"task_id": task_id, "label": "dog"},
                              headers={"Authorization": f"Bearer {annotator_token}"})
        assert r.status_code == 400

    async def test_empty_label_rejected(self, client: AsyncClient, annotator_token, manager_token, dataset_id):
        cr = await client.post(
            "/api/v1/tasks",
            json={"title": "Empty label test", "dataset_id": dataset_id,
                  "data": {}, "annotations_required": 1},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        task_id = cr.json()["id"]
        await client.put(f"/api/v1/tasks/{task_id}", json={"status": "active"},
                         headers={"Authorization": f"Bearer {manager_token}"})

        r = await client.post("/api/v1/annotations",
                              json={"task_id": task_id, "label": ""},
                              headers={"Authorization": f"Bearer {annotator_token}"})
        assert r.status_code == 422

    async def test_my_annotations(self, client: AsyncClient, annotator_token):
        r = await client.get("/api/v1/annotations/my",
                             headers={"Authorization": f"Bearer {annotator_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
