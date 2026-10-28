from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import CurrentUser, get_current_user
from app.models import Message, Thread

router = APIRouter(prefix="/api/threads", tags=["threads"])

THREAD_COLUMNS = "id,title,created_at,updated_at"


def get_thread_or_404(user: CurrentUser, thread_id: UUID, columns: str = THREAD_COLUMNS) -> dict:
    """Load a thread through the user's RLS-scoped client; other users' threads are invisible."""
    rows = user.db.table("threads").select(columns).eq("id", str(thread_id)).execute().data
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return rows[0]


@router.get("", response_model=list[Thread])
def list_threads(user: CurrentUser = Depends(get_current_user)):
    return (
        user.db.table("threads")
        .select(THREAD_COLUMNS)
        .order("updated_at", desc=True)
        .execute()
        .data
    )


@router.post("", response_model=Thread, status_code=status.HTTP_201_CREATED)
def create_thread(user: CurrentUser = Depends(get_current_user)):
    rows = user.db.table("threads").insert({"user_id": user.user_id}).execute().data
    return rows[0]


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: UUID, user: CurrentUser = Depends(get_current_user)):
    rows = user.db.table("threads").delete().eq("id", str(thread_id)).execute().data
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{thread_id}/messages", response_model=list[Message])
def list_messages(thread_id: UUID, user: CurrentUser = Depends(get_current_user)):
    get_thread_or_404(user, thread_id, columns="id")
    return (
        user.db.table("messages")
        .select("id,thread_id,role,content,created_at")
        .eq("thread_id", str(thread_id))
        .order("created_at")
        .execute()
        .data
    )
