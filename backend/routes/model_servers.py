from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/model_servers", tags=["Model Servers"])

@router.post("/", response_model=schemas.ModelServerRead, status_code=status.HTTP_201_CREATED)
async def create_model_server(server: schemas.ModelServerCreate, db: AsyncSession = Depends(get_db)):
    model_server = models.ModelServer(**server.dict())
    db.add(model_server)
    await db.commit()
    await db.refresh(model_server)
    return model_server

@router.get("/", response_model=List[schemas.ModelServerRead])
async def read_model_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ModelServer))
    return result.scalars().all()

@router.get("/{server_id}", response_model=schemas.ModelServerRead)
async def read_model_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ModelServer).where(models.ModelServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

@router.put("/{server_id}", response_model=schemas.ModelServerRead)
async def update_mcp_server(server_id: UUID, server: schemas.ModelServerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ModelServer).where(models.ModelServer.id == server_id))
    db_server = result.scalar_one_or_none()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    for field, value in server.dict().items():
        setattr(db_server, field, value)
    await db.commit()
    await db.refresh(db_server)
    return db_server

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ModelServer).where(models.ModelServer.id == server_id))
    db_server = result.scalar_one_or_none()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    await db.delete(db_server)
    await db.commit()
    return None
