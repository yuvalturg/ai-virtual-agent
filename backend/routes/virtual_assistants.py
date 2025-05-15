from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/virtual_assistants", tags=["virtual_assistants"])

@router.post("/", response_model=schemas.VirtualAssistantRead, status_code=status.HTTP_201_CREATED)
async def create_virtual_assistant(va: schemas.VirtualAssistantCreate, db: AsyncSession = Depends(get_db)):
    db_va = models.VirtualAssistant(
        name=va.name,
        prompt=va.prompt,
        model_name=va.model_name
    )
    db.add(db_va)
    await db.commit()
    await db.refresh(db_va)

    for kb_id in va.knowledge_base_ids:
        db.add(models.VirtualAssistantKnowledgeBase(
            virtual_assistant_id=db_va.id,
            knowledge_base_id=kb_id
        ))

    for tool_id in va.tool_ids:
        db.add(models.VirtualAssistantTool(
            virtual_assistant_id=db_va.id,
            tool_id=tool_id
        ))

    await db.commit()

    kb_result = await db.execute(select(models.VirtualAssistantKnowledgeBase).where(models.VirtualAssistantKnowledgeBase.virtual_assistant_id == db_va.id))
    kb_ids = [r.knowledge_base_id for r in kb_result.scalars().all()]

    tool_result = await db.execute(select(models.VirtualAssistantTool).where(models.VirtualAssistantTool.virtual_assistant_id == db_va.id))
    tool_ids = [r.tool_id for r in tool_result.scalars().all()]
    
    ret = {
        "id": db_va.id,
        "name": db_va.name,
        "prompt": db_va.prompt,
        "model_name": db_va.model_name,
        "created_by": db_va.created_by,
        "created_at": db_va.created_at,
        "updated_at": db_va.updated_at,
        "knowledge_base_ids": kb_ids,
        "tool_ids": tool_ids,
    }

    return ret

@router.get("/", response_model=List[schemas.VirtualAssistantRead])
async def get_virtual_assistants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant))
    assistants = result.scalars().all()
    ret = []
    for a in assistants:
        kb_result = await db.execute(select(models.VirtualAssistantKnowledgeBase).where(models.VirtualAssistantKnowledgeBase.virtual_assistant_id == a.id))
        kb_ids = [r.knowledge_base_id for r in kb_result.scalars().all()]

        tool_result = await db.execute(select(models.VirtualAssistantTool).where(models.VirtualAssistantTool.virtual_assistant_id == a.id))
        tool_ids = [r.tool_id for r in tool_result.scalars().all()]

        ret.append({
            "id": a.id,
            "name": a.name,
            "prompt": a.prompt,
            "model_name": a.model_name,
            "created_by": a.created_by,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "knowledge_base_ids": kb_ids,
            "tool_ids": tool_ids,
        })
    return ret


@router.get("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def read_virtual_assistant(va_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    va = result.scalar_one_or_none()
    if not va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")
    return va

@router.put("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def update_virtual_assistant(va_id: UUID, va: schemas.VirtualAssistantUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    db_va = result.scalar_one_or_none()
    if not db_va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")

    db_va.name = va.name
    db_va.prompt = va.prompt
    db_va.model_name = va.model_name

    db.query(models.VirtualAssistantKnowledgeBase).filter_by(virtual_assistant_id=db_va.id).delete()
    db.query(models.VirtualAssistantTool).filter_by(virtual_assistant_id=db_va.id).delete()

    for kb_id in va.knowledge_base_ids:
        db.add(models.VirtualAssistantKnowledgeBase(virtual_assistant_id=db_va.id, knowledge_base_id=kb_id))

    for tool_id in va.tool_ids:
        db.add(models.VirtualAssistantTool(virtual_assistant_id=db_va.id, tool_id=tool_id))

    await db.commit()
    await db.refresh(db_va)
    return db_va

@router.delete("/{va_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_virtual_assistant(va_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    db_va = result.scalar_one_or_none()
    if not db_va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")
    await db.delete(db_va)
    await db.commit()
    return None
