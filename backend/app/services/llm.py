from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from app.config import get_settings

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."

StreamEvent = tuple[str, dict[str, Any]]


@lru_cache
def get_client() -> OpenAI:
    settings = get_settings()
    return wrap_openai(
        OpenAI(api_key=settings.OPENROUTER_API_KEY, base_url=settings.OPENROUTER_BASE_URL)
    )


def build_messages(history: list[dict], user_text: str) -> list[dict[str, str]]:
    """Stateless completions: the model sees the system prompt, prior turns, then the new message."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *({"role": m["role"], "content": m["content"]} for m in history),
        {"role": "user", "content": user_text},
    ]


def _reduce_outputs(outputs: list[StreamEvent]) -> dict[str, Any]:
    """Collapse the streamed events into the final answer for the LangSmith run."""
    return {"output": "".join(data["text"] for kind, data in outputs if kind == "delta")}


@traceable(name="chat_turn", reduce_fn=_reduce_outputs)
def stream_reply(messages: list[dict[str, str]]) -> Iterator[StreamEvent]:
    stream = get_client().chat.completions.create(
        model=get_settings().OPENROUTER_MODEL, messages=messages, stream=True
    )

    for chunk in stream:
        # OpenRouter reports failures after the stream has started as a chunk with an error field.
        error = getattr(chunk, "error", None)
        if error:
            message = error.get("message") if isinstance(error, dict) else str(error)
            yield ("error", {"message": message or "Model error"})
            return
        if chunk.choices and chunk.choices[0].delta.content:
            yield ("delta", {"text": chunk.choices[0].delta.content})
    yield ("completed", {})
