"""
Knowledge Base API endpoints for managing vector databases and knowledge
sources.

This module provides CRUD operations for knowledge bases that are used for
Retrieval-Augmented Generation (RAG) functionality. Knowledge bases are
integrated with LlamaStack's vector database system for semantic search
and document retrieval.

Key Features:
- Create and manage knowledge bases with metadata
- Automatic synchronization with LlamaStack vector databases
- Support for external knowledge sources and configurations
- Vector database name as primary identifier for LlamaStack integration
- Read-only operations after creation (knowledge bases cannot be modified)
"""

import logging
import os
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..api.llamastack import get_client_from_request
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge_bases", tags=["knowledge_bases"])


@router.post(
    "/",
    response_model=schemas.KnowledgeBaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    kb: schemas.KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new knowledge base.

    This endpoint creates a new knowledge base in the database and
    automatically triggers synchronization with LlamaStack's vector database
    system.

    Args:
        kb: Knowledge base creation data including name, version, and
            configuration
        db: Database session dependency

    Returns:
        schemas.KnowledgeBaseRead: The created knowledge base with metadata

    Raises:
        HTTPException: If creation fails or validation errors occur
    """
    await create_ingestion_pipeline(kb)
    db_kb = models.KnowledgeBase(**kb.model_dump(exclude_unset=True))
    db.add(db_kb)
    await db.commit()
    await db.refresh(db_kb)

    db_kb.status = await get_pipeline_status(db_kb.vector_store_name)
    return db_kb


@router.get("/", response_model=List[schemas.KnowledgeBaseRead])
async def read_knowledge_bases(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Retrieve all knowledge bases from the database.

    This endpoint returns a list of all knowledge bases stored in the database,
    including their metadata and configuration details. It also fetches vector
    stores from LlamaStack to update vector_store_id fields.

    Args:
        request: FastAPI request object for LlamaStack client access
        db: Database session dependency

    Returns:
        List[schemas.KnowledgeBaseRead]: List of all knowledge bases
    """
    # Update vector_store_ids by matching with LlamaStack vector stores
    await update_vector_store_ids(request, db)

    # Select knowledge bases after updates
    result = await db.execute(select(models.KnowledgeBase))
    kbs = result.scalars().all()

    # Get pipeline status for each knowledge base
    for kb in kbs:
        kb.status = await get_pipeline_status(kb.vector_store_name)

    return kbs


@router.get("/{vector_store_name}", response_model=schemas.KnowledgeBaseRead)
async def read_knowledge_base(
    vector_store_name: str, db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific knowledge base by its vector database name.

    This endpoint fetches a single knowledge base using its vector database
    name as the unique identifier, which corresponds to the LlamaStack vector
    database.

    Args:
        vector_store_name: The unique vector database name/identifier
        db: Database session dependency

    Returns:
        schemas.KnowledgeBaseRead: The requested knowledge base

    Raises:
        HTTPException: 404 if the knowledge base is not found
    """
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.vector_store_name == vector_store_name
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    kb.status = await get_pipeline_status(kb.vector_store_name)
    return kb


@router.delete("/{vector_store_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    vector_store_name: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Delete a knowledge base from both the database and LlamaStack.

    This endpoint removes a knowledge base from the local database and attempts
    to unregister it from LlamaStack's vector database system. If LlamaStack
    deletion fails, the database deletion will still proceed to handle cases
    where the knowledge base is in PENDING status.

    Args:
        vector_store_name: The vector database name/identifier of the
                       knowledge base to delete
        db: Database session dependency

    Raises:
        HTTPException: 404 if the knowledge base is not found in the database

    Returns:
        None: 204 No Content on successful deletion
    """
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.vector_store_name == vector_store_name
        )
    )
    db_kb = result.scalar_one_or_none()
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    kb_name = db_kb.name  # Store name before deletion

    # First, try to delete from LlamaStack using vector_store_id if available
    if db_kb.vector_store_id:
        client = get_client_from_request(request)
        try:
            logger.info(
                f"Deleting knowledge base from LlamaStack using ID: {db_kb.vector_store_id}"
            )
            await client.vector_stores.delete(db_kb.vector_store_id)
            logger.info(
                f"Successfully deleted from LlamaStack: {db_kb.vector_store_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to delete from LlamaStack: {str(e)}")
    else:
        logger.info(
            f"No vector_store_id found for {vector_store_name}, skipping LlamaStack deletion"
        )

    try:
        await delete_ingestion_pipeline(vector_store_name)
    except Exception as e:
        logger.warning(f"failed to delete ingestion pipeline: {str(e)}")

    # Then delete from database
    await db.delete(db_kb)
    await db.commit()

    logger.info(f"Successfully deleted knowledge base from database: {kb_name}")
    return None


async def create_ingestion_pipeline(kb: schemas.KnowledgeBaseCreate):
    """
    Internal method that creates a pipeline or a pipeline revision,
    and runs it.

    This method takes in a KnowledgebaseCreate object and converts it
    to a pipeline creation dictionary. It then calls the ingestion-pipeline
    API service to add a new pipeline and trigger a run.

    Args:
        kb: KnowledgeBaseCreate with all the relevant source information

    Returns:
        None

    Raises:
        Exception: If the ingestion-pipeline API call fails
    """
    add_pipeline = os.environ["INGESTION_PIPELINE_URL"] + "/add"
    data = kb.pipeline_model_dict()
    logger.info(f"Creating pipeline at {add_pipeline} {data=}")
    async with httpx.AsyncClient() as client:
        response = await client.post(add_pipeline, json=data)
        response.raise_for_status()


async def delete_ingestion_pipeline(vector_store_name: str):
    """
    Internal method that deletes an existing pipeline

    This method takes a vector_store_name and calls the ingestion-pipeline
    API service to delete the pipeline including all runs and
    versions.

    Args:
        vector_store_name: The actual pipeline_name

    Returns:
        None

    Raises:
        Exception: If the ingestion-pipeline API call fails
    """
    del_pipeline = os.environ["INGESTION_PIPELINE_URL"] + "/delete"
    data = {"pipeline_name": vector_store_name}
    logger.info(f"Deleting pipeline with {del_pipeline} {data=}")
    async with httpx.AsyncClient() as client:
        response = await client.delete(del_pipeline, params=data)
        response.raise_for_status()


async def update_vector_store_ids(request: Request, db: AsyncSession):
    """
    Update vector_store_id fields by matching knowledge bases with LlamaStack vector stores.

    This function fetches all vector stores from LlamaStack and matches them with
    knowledge bases by vector_store_name. When a match is found, it updates the
    vector_store_id field in the database.

    Args:
        kbs: List of knowledge base objects from database
        request: FastAPI request object for LlamaStack client access
        db: Database session for updating records

    Returns:
        None
    """
    try:
        client = get_client_from_request(request)
        vector_stores = await client.vector_stores.list()

        # Create a mapping of vector store names to IDs
        vs_name_to_id = {}
        for vs in vector_stores.data:
            vs_name_to_id[vs.name] = vs.id

        # Get only knowledge bases that exist in LlamaStack vector stores
        result = await db.execute(
            select(models.KnowledgeBase).where(
                models.KnowledgeBase.vector_store_name.in_(vs_name_to_id.keys())
            )
        )
        kbs = result.scalars().all()

        # Update knowledge bases that need vector_store_id updates
        updates_made = False
        for kb in kbs:
            vs_id = vs_name_to_id[kb.vector_store_name]  # We know it exists now
            if kb.vector_store_id != vs_id:
                kb.vector_store_id = vs_id
                updates_made = True
                logger.info(
                    f"Updated vector_store_id for {kb.vector_store_name}: {vs_id}"
                )

        # Commit all updates if any were made
        if updates_made:
            await db.commit()

    except Exception as e:
        logger.warning(f"Failed to update vector_store_ids from LlamaStack: {str(e)}")


async def get_pipeline_status(pipeline_name: str) -> str:
    """
    Retrieve ingestion pipeline status by pipeline name.

    This endpoint fetches the given ingestion pipeline state from the
    ingestion-pipeline service API.

    Args:
        pipeline_name: Pipeline name (vector_store_name)

    Returns:
        str: The requested ingestion pipeline state

    Raises:
        Exception: If the ingestion-pipeline API call fails
    """
    status_endpoint = os.environ["INGESTION_PIPELINE_URL"] + "/status"
    data = {"pipeline_name": pipeline_name}
    logger.info(f"Fetching pipeline status from {status_endpoint} {data=}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(status_endpoint, params=data)
            response.raise_for_status()
            return response.json().get("state", "unknown")
        except Exception as e:
            logger.error(
                f"could not fetch pipeline status for {pipeline_name}: {str(e)}"
            )
            return "unknown"
