"""
CRUD operations for Knowledge Bases.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import KnowledgeBase
from ..schemas import KnowledgeBaseCreate
from .base import CRUDBase


class CRUDKnowledgeBase(CRUDBase[KnowledgeBase, KnowledgeBaseCreate, dict]):
    async def create(
        self, db: AsyncSession, *, obj_in: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        """Create knowledge base with transaction management."""
        try:
            db_obj = KnowledgeBase(
                vector_store_name=obj_in.vector_store_name,
                vector_store_id=obj_in.vector_store_id,
                name=obj_in.name,
                version=obj_in.version,
                embedding_model=obj_in.embedding_model,
                provider_id=obj_in.provider_id,
                is_external=obj_in.is_external,
                status=obj_in.status,
                source=obj_in.source,
                source_configuration=obj_in.source_configuration,
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception:
            await db.rollback()
            raise

    async def get_by_vector_store_name(
        self, db: AsyncSession, *, vector_store_name: str
    ) -> Optional[KnowledgeBase]:
        """Get knowledge base by vector store name."""
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.vector_store_name == vector_store_name
            )
        )
        return result.scalar_one_or_none()


knowledge_bases = CRUDKnowledgeBase(KnowledgeBase)
