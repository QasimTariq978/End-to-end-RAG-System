from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_threads_require_auth():
    assert client.get("/api/threads").status_code == 401
    assert client.get("/api/threads", headers={"Authorization": "Basic abc"}).status_code == 401
