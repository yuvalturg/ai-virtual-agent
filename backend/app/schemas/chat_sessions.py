"""Schemas for chat sessions API."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from .chat import ChatMessageResponse


class CreateSessionRequest(BaseModel):
    """Request model for creating new chat sessions."""

    agent_id: UUID
    session_name: Optional[str] = None


class PaginationInfo(BaseModel):
    """Pagination information."""

    page: int
    page_size: int
    total_messages: int
    has_more: bool
    messages_loaded: int


class ChatSessionSummary(BaseModel):
    """Chat session summary for list views."""

    id: UUID
    title: str
    agent_name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_response_id: Optional[str] = None


class ChatSessionDetail(BaseModel):
    """Detailed chat session with messages."""

    id: UUID
    title: str
    agent_name: str
    agent_id: UUID
    messages: List[ChatMessageResponse]
    created_at: str
    updated_at: str
    last_response_id: Optional[str] = None
    pagination: Optional[PaginationInfo] = None


class DeleteSessionResponse(BaseModel):
    """Response for session deletion."""

    message: str
