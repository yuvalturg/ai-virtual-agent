from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/guardrails", tags=["guardrails"])

@router.post("/", response_model=schemas.GuardrailRead, status_code=status.HTTP_201_CREATED)
async def create_guardrail(item: schemas.GuardrailCreate, db: AsyncSession = Depends(get_db)):
    db_item = models.Guardrail(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[schemas.GuardrailRead])
async def read_guardrails(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Guardrail))
    return result.scalars().all()

@router.get("/{guardrail_id}", response_model=schemas.GuardrailRead)
async def read_guardrail(guardrail_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Guardrail).where(models.Guardrail.id == guardrail_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return item

@router.put("/{guardrail_id}", response_model=schemas.GuardrailRead)
async def update_guardrail(guardrail_id: UUID, item: schemas.GuardrailCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Guardrail).where(models.Guardrail.id == guardrail_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    for field, value in item.dict().items():
        setattr(db_item, field, value)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.delete("/{guardrail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardrail(guardrail_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Guardrail).where(models.Guardrail.id == guardrail_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    await db.delete(db_item)
    await db.commit()
    return None
