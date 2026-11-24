from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.modules.tasks import service as tasks_service


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(tasks_service.notify_task_created, "delay", lambda **kwargs: None)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _register_and_login(client: TestClient, email: str, password: str = "secret123") -> dict[str, str]:
    reg_res = client.post("/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201

    login_res = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_register_login(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    headers = _register_and_login(client, "user1@example.com")
    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "user1@example.com"
    assert me.json()["role"] == "user"


def test_rbac_and_foreign_project_access(client: TestClient):
    user1_headers = _register_and_login(client, "owner@example.com")
    user2_headers = _register_and_login(client, "other@example.com")

    forbidden_users = client.get("/users/", headers=user1_headers)
    assert forbidden_users.status_code == 403

    proj_res = client.post(
        "/projects/",
        json={"title": "API Project", "description": "Test project"},
        headers=user1_headers,
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    foreign_task_res = client.post(
        "/tasks/",
        json={"title": "Hack task", "project_id": project_id},
        headers=user2_headers,
    )
    assert foreign_task_res.status_code == 403


def test_projects_and_tasks_crud(client: TestClient):
    headers = _register_and_login(client, "pm@example.com")

    proj = client.post(
        "/projects/",
        json={"title": "Backend Sprint", "description": "FastAPI tasks"},
        headers=headers,
    )
    assert proj.status_code == 201
    project_id = proj.json()["id"]

    task = client.post(
        "/tasks/",
        json={
            "title": "Write tests",
            "description": "Cover CRUD and auth",
            "status": "todo",
            "project_id": project_id,
        },
        headers=headers,
    )
    assert task.status_code == 201
    task_id = task.json()["id"]
    assert task.json()["status"] == "todo"

    upd = client.patch(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "done"

    listed = client.get(f"/tasks/?project_id={project_id}", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    del_task = client.delete(f"/tasks/{task_id}", headers=headers)
    assert del_task.status_code == 204

    del_proj = client.delete(f"/projects/{project_id}", headers=headers)
    assert del_proj.status_code == 204