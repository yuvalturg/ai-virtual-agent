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
    db_va = models.VirtualAssistant(**va.dict())
    db.add(db_va)
    await db.commit()
    await db.refresh(db_va)
    return db_va

@router.get("/", response_model=List[schemas.VirtualAssistantRead])
async def read_virtual_assistants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant))
    return result.scalars().all()

@router.get("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def read_virtual_assistant(va_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    va = result.scalar_one_or_none()
    if not va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")
    return va

@router.put("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def update_virtual_assistant(va_id: UUID, va: schemas.VirtualAssistantCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    db_va = result.scalar_one_or_none()
    if not db_va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")
    for field, value in va.dict().items():
        setattr(db_va, field, value)
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
