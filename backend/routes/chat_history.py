from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/chat_history", tags=["chat_history"])

@router.post("/", response_model=schemas.ChatHistoryRead, status_code=status.HTTP_201_CREATED)
async def create_chat_history(item: schemas.ChatHistoryCreate, db: AsyncSession = Depends(get_db)):
    db_item = models.ChatHistory(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[schemas.ChatHistoryRead])
async def read_chat_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ChatHistory))
    return result.scalars().all()

@router.get("/{chat_id}", response_model=schemas.ChatHistoryRead)
async def read_chat_item(chat_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ChatHistory).where(models.ChatHistory.id == chat_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return item

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_item(chat_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ChatHistory).where(models.ChatHistory.id == chat_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Chat history not found")
    await db.delete(item)
    await db.commit()
    return None
