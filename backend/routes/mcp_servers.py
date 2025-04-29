from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/mcp_servers", tags=["mcp_servers"])

@router.post("/", response_model=schemas.MCPServerRead, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(server: schemas.MCPServerCreate, db: AsyncSession = Depends(get_db)):
    db_server = models.MCPServer(**server.dict())
    db.add(db_server)
    await db.commit()
    await db.refresh(db_server)
    return db_server

@router.get("/", response_model=List[schemas.MCPServerRead])
async def read_mcp_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MCPServer))
    return result.scalars().all()

@router.get("/{server_id}", response_model=schemas.MCPServerRead)
async def read_mcp_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MCPServer).where(models.MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

@router.put("/{server_id}", response_model=schemas.MCPServerRead)
async def update_mcp_server(server_id: UUID, server: schemas.MCPServerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MCPServer).where(models.MCPServer.id == server_id))
    db_server = result.scalar_one_or_none()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    for field, value in server.dict().items():
        setattr(db_server, field, value)
    await db.commit()
    await db.refresh(db_server)
    return db_server

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MCPServer).where(models.MCPServer.id == server_id))
    db_server = result.scalar_one_or_none()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    await db.delete(db_server)
    await db.commit()
    return None
