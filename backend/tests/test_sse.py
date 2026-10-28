from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.main import app
from app.routers import chat

THREAD_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def db():
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.return_value.data = [{"id": "msg-1"}]
    # History query returns newest first.
    history_query = db.table.return_value.select.return_value.eq.return_value.order.return_value
    history_query.limit.return_value.execute.return_value.data = [
        {"role": "assistant", "content": "earlier reply"},
        {"role": "user", "content": "earlier question"},
    ]
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(user_id="user-1", db=db)
    yield db
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_thread(monkeypatch):
    monkeypatch.setattr(
        chat,
        "get_thread_or_404",
        lambda *a, **k: {"id": THREAD_ID, "title": "New chat"},
    )


def post(content="hello"):
    return TestClient(app).post(f"/api/threads/{THREAD_ID}/messages", json={"content": content})


def test_history_sent_oldest_first_before_new_message(monkeypatch, db):
    sent = []

    def fake_reply(messages):
        sent.extend(messages)
        yield ("completed", {})

    monkeypatch.setattr(chat.llm, "stream_reply", fake_reply)
    post("new question")

    assert [m["content"] for m in sent[1:]] == ["earlier question", "earlier reply", "new question"]


def test_streams_delta_then_done(monkeypatch, db):
    def fake_reply(messages):
        yield ("tool", {"name": "search", "status": "searching"})
        yield ("delta", {"text": "Hel"})
        yield ("delta", {"text": "lo"})
        yield ("completed", {})

    monkeypatch.setattr(chat.llm, "stream_reply", fake_reply)
    response = post()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert body.index("event: tool") < body.index("event: delta") < body.index("event: done")
    assert 'data: {"message_id": "msg-1"}' in body

    inserted = [c.args[0] for c in db.table.return_value.insert.call_args_list]
    assert inserted[0]["role"] == "user"
    assert inserted[-1] == {
        "thread_id": THREAD_ID,
        "user_id": "user-1",
        "role": "assistant",
        "content": "Hello",
    }


def test_error_does_not_save_assistant_message(monkeypatch, db):
    def fake_reply(messages):
        yield ("delta", {"text": "partial"})
        yield ("error", {"message": "boom"})

    monkeypatch.setattr(chat.llm, "stream_reply", fake_reply)
    body = post().text

    assert "event: error" in body and "event: done" not in body
    roles = [c.args[0]["role"] for c in db.table.return_value.insert.call_args_list]
    assert roles == ["user"]


def test_empty_content_rejected(db):
    assert post(content="").status_code == 422
