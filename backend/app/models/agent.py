"""
Agent-related models: VirtualAgent, AgentTemplate, TemplateSuite.
"""

from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, String, func
from sqlalchemy.orm import relationship

from .base import Base


class VirtualAgent(Base):
    """
    Store virtual agent configurations for use with Responses API.

    Since the Responses API doesn't persist agents like the old Agents API,
    we store the virtual agent configurations locally and use them when
    creating responses.
    """

    __tablename__ = "virtual_agents"

    id = Column(String(255), primary_key=True)  # UUID as string
    name = Column(String(255), nullable=False, unique=True)
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
