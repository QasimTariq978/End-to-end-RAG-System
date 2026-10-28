from types import SimpleNamespace

from app.services import llm


def test_messages_are_system_then_history_then_user():
    history = [
        {"role": "user", "content": "hi", "id": "ignored"},
        {"role": "assistant", "content": "hello"},
    ]
    messages = llm.build_messages(history, "how are you?")

    assert messages == [
        {"role": "system", "content": llm.SYSTEM_PROMPT},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "how are you?"},
    ]


def test_no_history_sends_system_and_user_only():
    assert [m["role"] for m in llm.build_messages([], "hi")] == ["system", "user"]


def chunk(content=None, error=None):
    delta = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)] if content is not None else [], error=error)


def fake_client(monkeypatch, chunks):
    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return iter(chunks)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "get_client", lambda: client)
    return calls


def test_stream_yields_deltas_then_completed(monkeypatch):
    calls = fake_client(monkeypatch, [chunk("Hel"), chunk(""), chunk("lo"), chunk()])
    events = list(llm.stream_reply([{"role": "user", "content": "hi"}]))

    assert events == [("delta", {"text": "Hel"}), ("delta", {"text": "lo"}), ("completed", {})]
    assert calls["stream"] is True and calls["model"] == llm.get_settings().OPENROUTER_MODEL


def test_stream_error_chunk_stops_without_completed(monkeypatch):
    fake_client(monkeypatch, [chunk("par"), chunk(error={"message": "rate limited"})])
    events = list(llm.stream_reply([]))

    assert events == [("delta", {"text": "par"}), ("error", {"message": "rate limited"})]
