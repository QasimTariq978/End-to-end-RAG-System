from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Thread(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    id: UUID
    thread_id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)
