import os
import tempfile

# Use an isolated DB for tests (must be set before importing the app)
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _auth(client, username="alice"):
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "secret123"},
    )
    r = client.post("/auth/login", data={"username": username, "password": "secret123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_duplicate_and_bad_login(client):
    _auth(client)
    r = client.post(
        "/auth/register",
        json={"username": "alice", "email": "x@example.com", "password": "secret123"},
    )
    assert r.status_code == 409
    r = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_requires_auth(client):
    assert client.get("/tasks").status_code == 401


def test_task_crud_and_filters(client):
    h = _auth(client)
    t = client.post("/tasks", json={"title": "Write code"}, headers=h)
    assert t.status_code == 201
    tid = t.json()["id"]
    client.post("/tasks", json={"title": "Done thing", "completed": True}, headers=h)

    assert client.get(f"/tasks/{tid}", headers=h).json()["title"] == "Write code"
    assert client.get("/tasks?status=pending", headers=h).json()["total"] == 1
    assert client.get("/tasks?status=completed", headers=h).json()["total"] == 1
    assert client.get("/tasks", headers=h).json()["total"] == 2

    r = client.patch(f"/tasks/{tid}", json={"title": "Write better code"}, headers=h)
    assert r.json()["title"] == "Write better code"
    assert client.patch(f"/tasks/{tid}/toggle", headers=h).json()["completed"] is True

    assert client.delete(f"/tasks/{tid}", headers=h).status_code == 204
    assert client.get(f"/tasks/{tid}", headers=h).status_code == 404


def test_validation_and_isolation(client):
    a, b = _auth(client, "alice"), _auth(client, "bob")
    r = client.post("/tasks", json={"title": "   "}, headers=a)
    assert r.status_code == 422 and r.json()["error"]["details"]
    tid = client.post("/tasks", json={"title": "private"}, headers=a).json()["id"]
    assert client.get(f"/tasks/{tid}", headers=b).status_code == 404
    assert client.delete(f"/tasks/{tid}", headers=b).status_code == 404
