"""
CRUD operations for Chat models.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ChatMessage, ChatSession
from ..schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
)
from .base import CRUDBase


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    """CRUD operations for ChatSession."""

    async def get_by_agent(
        self, db: AsyncSession, *, agent_id: str, skip: int = 0, limit: int = 50
    ) -> List[ChatSession]:
        """Get chat sessions for a specific agent."""
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.agent_id == agent_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_messages(
        self, db: AsyncSession, *, session_id: str
    ) -> Optional[ChatSession]:
        """Get chat session with all messages."""
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()


class CRUDChatMessage(CRUDBase[ChatMessage, dict, dict]):
    """CRUD operations for ChatMessage."""

    async def get_by_session(
        self, db: AsyncSession, *, session_id: str, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        """Get messages for a specific session."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_session_message_count(
        self, db: AsyncSession, *, session_id: str
    ) -> int:
        """Get total message count for a session."""
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        messages = result.scalars().all()
        return len(messages)

    async def get_latest_by_session(
        self, db: AsyncSession, *, session_id: str, limit: int = 10
    ) -> List[ChatMessage]:
        """Get latest messages for a session."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


chat_session = CRUDChatSession(ChatSession)
chat_message = CRUDChatMessage(ChatMessage)
