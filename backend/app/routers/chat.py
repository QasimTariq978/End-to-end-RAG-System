import json
import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth import CurrentUser, get_current_user
from app.models import SendMessageRequest
from app.routers.threads import get_thread_or_404
from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threads", tags=["chat"])

NEW_THREAD_TITLE = "New chat"
HISTORY_LIMIT = 50


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/{thread_id}/messages")
def send_message(
    thread_id: UUID,
    body: SendMessageRequest,
    user: CurrentUser = Depends(get_current_user),
):
    thread = get_thread_or_404(user, thread_id, columns="id,title")
    # Load prior turns before saving the new message so it isn't sent twice.
    recent = (
        user.db.table("messages")
        .select("role,content")
        .eq("thread_id", str(thread_id))
        .order("created_at", desc=True)
        .limit(HISTORY_LIMIT)
        .execute()
        .data
    )
    messages = llm.build_messages(list(reversed(recent)), body.content)

    user.db.table("messages").insert(
        {"thread_id": str(thread_id), "user_id": user.user_id, "role": "user", "content": body.content}
    ).execute()
    if thread["title"] == NEW_THREAD_TITLE:
        user.db.table("threads").update({"title": body.content[:50]}).eq(
            "id", str(thread_id)
        ).execute()

    def gen() -> Iterator[str]:
        parts: list[str] = []
        completed = errored = False
        try:
            # Drain the stream instead of returning early: closing the traced generator
            # mid-iteration raises GeneratorExit and LangSmith records the run as an error.
            for kind, data in llm.stream_reply(messages):
                if kind == "delta":
                    parts.append(data["text"])
                    yield sse("delta", data)
                elif kind == "tool":
                    yield sse("tool", data)
                elif kind == "error":
                    errored = True
                    yield sse("error", data)
                elif kind == "completed":
                    completed = True
            if not completed:
                if not errored:
                    yield sse("error", {"message": "Stream ended before the response completed"})
                return
            rows = (
                user.db.table("messages")
                .insert(
                    {
                        "thread_id": str(thread_id),
                        "user_id": user.user_id,
                        "role": "assistant",
                        "content": "".join(parts),
                    }
                )
                .execute()
                .data
            )
            user.db.table("threads").update(
                {"updated_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", str(thread_id)).execute()
            yield sse("done", {"message_id": rows[0]["id"]})
        except Exception as exc:
            logger.exception("Chat stream failed")
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
