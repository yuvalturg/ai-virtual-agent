from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/knowledge_bases", tags=["knowledge_bases"])

@router.post("/", response_model=schemas.KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(kb: schemas.KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    db_kb = models.KnowledgeBase(**kb.dict())
    db.add(db_kb)
    await db.commit()
    await db.refresh(db_kb)
    return db_kb

@router.get("/", response_model=List[schemas.KnowledgeBaseRead])
async def read_knowledge_bases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.KnowledgeBase))
    return result.scalars().all()

@router.get("/{kb_id}", response_model=schemas.KnowledgeBaseRead)
async def read_knowledge_base(kb_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.KnowledgeBase).where(models.KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@router.put("/{kb_id}", response_model=schemas.KnowledgeBaseRead)
async def update_knowledge_base(kb_id: UUID, kb: schemas.KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.KnowledgeBase).where(models.KnowledgeBase.id == kb_id))
    db_kb = result.scalar_one_or_none()
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    for field, value in kb.dict().items():
        setattr(db_kb, field, value)
    await db.commit()
    await db.refresh(db_kb)
    return db_kb

@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(kb_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.KnowledgeBase).where(models.KnowledgeBase.id == kb_id))
    db_kb = result.scalar_one_or_none()
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    await db.delete(db_kb)
    await db.commit()
    return None
