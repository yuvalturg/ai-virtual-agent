"""
SQLAlchemy database models for the AI Virtual Agent Quickstart application.

This module defines the database schema and relationships for:
- Users and authentication
- Chat sessions and conversation history
- Knowledge bases and document storage
- Virtual agents and chat sessions
- MCP servers and tool configurations
- Agent templates and configurations

All models use async SQLAlchemy with PostgreSQL and include
appropriate indexes and relationships for optimal performance.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    user = "user"
    devops = "devops"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum(RoleEnum, name="role"), nullable=False)
    agent_ids = Column(JSON, nullable=False, default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    knowledge_bases = relationship("KnowledgeBase", back_populates="creator")
    guardrails = relationship("Guardrail", back_populates="creator")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    vector_store_name = Column(String(255), primary_key=True)
    vector_store_id = Column(
        String(255), nullable=True
    )  # LlamaStack vector store ID (vs_xxxx format)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    embedding_model = Column(String(255), nullable=False)
    provider_id = Column(String(255))
    is_external = Column(Boolean, nullable=False, default=False)
    status = Column(String(50), nullable=True)
    source = Column(String(255))
    source_configuration = Column(JSON)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    creator = relationship("User", back_populates="knowledge_bases")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String(255), primary_key=True)
    session_state = Column(JSON, default=dict)

    # New fields for sidebar display
    title = Column(String(500), nullable=True)  # Generated summary/title
    agent_id = Column(
        String(255),
        ForeignKey("virtual_agent_configs.id", ondelete="CASCADE"),
        nullable=True,
    )  # Agent ID

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship to chat messages
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    # Relationship to virtual agent
    agent = relationship("VirtualAgentConfig")


class ChatMessage(Base):
    """
    Store individual messages in a chat session.

    This provides persistent message storage, allowing us to send full
    conversation context following OpenAI's recommended approach.
    """

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        String(255), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Message metadata
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(JSON, nullable=False)  # List of content items (text, images, etc.)

    # Optional response metadata
    response_id = Column(
        String(255), nullable=True
    )  # LlamaStack response ID for reference

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class Guardrail(Base):
    __tablename__ = "guardrails"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    rules = Column(JSON, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    creator = relationship("User", back_populates="guardrails")


class VirtualAgentConfig(Base):
    """
    Store virtual agent configurations for use with Responses API.

    Since the Responses API doesn't persist agents like the old Agents API,
    we store the virtual agent configurations locally and use them when
    creating responses.
    """

    __tablename__ = "virtual_agent_configs"

    id = Column(String(255), primary_key=True)  # UUID as string
    name = Column(String(255), nullable=False)
    model_name = Column(String(255), nullable=False)
    template_id = Column(
        String(255),
        ForeignKey("agent_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt = Column(String, nullable=True)
    tools = Column(JSON, nullable=True, default=list)
    knowledge_base_ids = Column(JSON, nullable=True, default=list)  # vector_store_names
    vector_store_ids = Column(
        JSON, nullable=True, default=list
    )  # actual LlamaStack vector store IDs
    input_shields = Column(JSON, nullable=True, default=list)
    output_shields = Column(JSON, nullable=True, default=list)
    sampling_strategy = Column(String(50), nullable=True)
    temperature = Column(JSON, nullable=True)  # Using JSON to handle float/None
    top_p = Column(JSON, nullable=True)
    top_k = Column(JSON, nullable=True)
    max_tokens = Column(JSON, nullable=True)
    repetition_penalty = Column(JSON, nullable=True)
    max_infer_iters = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship to template
    template = relationship("AgentTemplate")


class TemplateSuite(Base):
    __tablename__ = "template_suites"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship to agent templates
    templates = relationship(
        "AgentTemplate", back_populates="suite", cascade="all, delete-orphan"
    )


class AgentTemplate(Base):
    __tablename__ = "agent_templates"

    id = Column(String(255), primary_key=True)
    suite_id = Column(
        String(255),
        ForeignKey("template_suites.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    suite = relationship("TemplateSuite", back_populates="templates")
