from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/virtual_assistants", tags=["virtual_assistants"])

@router.post("/", response_model=schemas.VirtualAssistantRead, status_code=status.HTTP_201_CREATED)
async def create_virtual_assistant(va: schemas.VirtualAssistantCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_va = models.VirtualAssistant(
            name=va.name,
            prompt=va.prompt,
            model_name=va.model_name
        )
        db.add(db_va)

        await db.flush()

        if not db_va.id:
            await db.rollback() 
            raise Exception("Virtual Assistant ID not generated after flush.")

        if va.knowledge_base_ids: # Process only if the list is not empty
            knowledge_base_associations = []
            for vector_db_name in va.knowledge_base_ids:
                # Check if knowledge base exists using vector_db_name
                kb_result = await db.execute(
                    select(models.KnowledgeBase).where(models.KnowledgeBase.vector_db_name == vector_db_name)
                )
                kb_exists = kb_result.scalar_one_or_none()
                if not kb_exists:
                     await db.rollback()
                     raise HTTPException(status_code=404, detail=f"KnowledgeBase with vector_db_name {vector_db_name} not found.")
                association = models.VirtualAssistantKnowledgeBase(
                    virtual_assistant_id=db_va.id,
                    vector_db_name=vector_db_name  # Now uses vector_db_name directly
                )
                knowledge_base_associations.append(association)
            db.add_all(knowledge_base_associations)

        if va.tools:
            tool_associations = []
            for tool_info in va.tools: # tool_info is a schemas.ToolAssociationInfo object
                association = models.VirtualAssistantTool(
                    virtual_assistant_id=db_va.id,
                    toolgroup_id=tool_info.toolgroup_id # Use tool_info.toolgroup_id
                )
                tool_associations.append(association)
            db.add_all(tool_associations)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"ERROR: create_virtual_assistant: {str(e)}") # Example logging
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    ret = {
        "id": db_va.id,
        "name": db_va.name,
        "prompt": db_va.prompt,
        "model_name": db_va.model_name,
        "created_by": db_va.created_by,
        "created_at": db_va.created_at,
        "updated_at": db_va.updated_at,
        "knowledge_base_ids": va.knowledge_base_ids,  # Now list of vector_db_names
        "tools": va.tools,  # List of ToolAssociationInfo objects
    }

    return ret

@router.get("/", response_model=List[schemas.VirtualAssistantRead])
async def get_virtual_assistants(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(models.VirtualAssistant)
        .options(
            # Ensure these relationship names match what's in your VirtualAssistant model
            selectinload(models.VirtualAssistant.knowledge_bases), # This loads VirtualAssistantKnowledgeBase objects
            selectinload(models.VirtualAssistant.tools)            # This loads VirtualAssistantTool objects
        )
    )
    result = await db.execute(stmt)
    # .unique() helps ensure distinct VirtualAssistant instances if joins cause duplicates
    assistants = result.scalars().unique().all() 
    
    response_list = []
    for assistant_model in assistants: # Renamed 'a' to 'assistant_model' for clarity
        # Extract knowledge base vector_db_names from the preloaded 'knowledge_bases' relationship
        # 'assistant_model.knowledge_bases' contains VirtualAssistantKnowledgeBase instances
        kb_ids = [
            kb_assoc.vector_db_name 
            for kb_assoc in assistant_model.knowledge_bases
        ]
        
        # Extract tool information from the preloaded 'tools' relationship
        # 'assistant_model.tools' contains VirtualAssistantTool instances
        tools_info = [
            schemas.ToolAssociationInfo(
                toolgroup_id=tool_assoc.toolgroup_id
            ) 
            for tool_assoc in assistant_model.tools
        ]
        
        response_list.append(schemas.VirtualAssistantRead(
            id=assistant_model.id,
            name=assistant_model.name,
            prompt=assistant_model.prompt,
            model_name=assistant_model.model_name,
            created_by=assistant_model.created_by,
            created_at=assistant_model.created_at,
            updated_at=assistant_model.updated_at,
            knowledge_base_ids=kb_ids,
            tools=tools_info  # Use the 'tools' field with the correct structure
        ))
    return response_list


@router.get("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def read_virtual_assistant(va_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(models.VirtualAssistant)
        .where(models.VirtualAssistant.id == va_id)
        .options(
            selectinload(models.VirtualAssistant.knowledge_bases), # Preload KB associations
            selectinload(models.VirtualAssistant.tools)            # Preload Tool associations
        )
    )
    result = await db.execute(stmt)
    db_va = result.scalars().unique().one_or_none() # .unique() is good practice

    if not db_va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual assistant not found")

    # Extract knowledge base vector_db_names from the preloaded relationship
    kb_ids = [
        kb_assoc.vector_db_name 
        for kb_assoc in db_va.knowledge_bases
    ]
    
    # Extract tool information from the preloaded relationship
    tools_info = [
        schemas.ToolAssociationInfo(
            toolgroup_id=tool_assoc.toolgroup_id
        )
        for tool_assoc in db_va.tools
    ]

    return schemas.VirtualAssistantRead(
        id=db_va.id,
        name=db_va.name,
        prompt=db_va.prompt,
        model_name=db_va.model_name,
        created_by=db_va.created_by,
        created_at=db_va.created_at,
        updated_at=db_va.updated_at,
        knowledge_base_ids=kb_ids,
        tools=tools_info # Use the 'tools' field with the correct structure
    )

@router.put("/{va_id}", response_model=schemas.VirtualAssistantRead)
async def update_virtual_assistant(va_id: UUID, va_update_payload: schemas.VirtualAssistantUpdate, db: AsyncSession = Depends(get_db)):
    stmt_get_va = (
        select(models.VirtualAssistant)
        .where(models.VirtualAssistant.id == va_id)
    )
    result = await db.execute(stmt_get_va)
    db_va = result.scalar_one_or_none()

    if not db_va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual assistant not found")

    # Get update data, excluding unset fields to support PATCH-like behavior
    update_data = va_update_payload.model_dump(exclude_unset=True)

    # Update basic attributes of VirtualAssistant
    allowed_fields = ["name", "prompt", "model_name"]  # Explicitly list allowed fields
    for field, value in update_data.items():
        # Only update explicitly allowed fields, avoid relationship fields
        if field in allowed_fields:
            setattr(db_va, field, value)

    # Handle Knowledge Base Associations
    if "knowledge_base_ids" in update_data and update_data["knowledge_base_ids"] is not None:
        # Delete existing knowledge base associations for this VA
        await db.execute(
            delete(models.VirtualAssistantKnowledgeBase)
            .where(models.VirtualAssistantKnowledgeBase.virtual_assistant_id == db_va.id)
        )
        # Add new associations from the payload
        if update_data["knowledge_base_ids"]: # Ensure there are IDs to process
            kb_associations_to_add = []
            for vector_db_name in update_data["knowledge_base_ids"]: # Now vector_db_name strings
                # Check if knowledge base exists using vector_db_name
                kb_result = await db.execute(
                    select(models.KnowledgeBase).where(models.KnowledgeBase.vector_db_name == vector_db_name)
                )
                kb_exists = kb_result.scalar_one_or_none()
                if not kb_exists:
                    await db.rollback()
                    raise HTTPException(status_code=404, detail=f"KnowledgeBase with vector_db_name {vector_db_name} not found.")
                kb_associations_to_add.append(
                    models.VirtualAssistantKnowledgeBase(virtual_assistant_id=db_va.id, vector_db_name=vector_db_name)
                )
            db.add_all(kb_associations_to_add)

    # Handle Tool Associations
    if "tools" in update_data and update_data["tools"] is not None: # Check for 'tools', not 'tool_ids'
        # Delete existing tool associations for this VA
        await db.execute(
            delete(models.VirtualAssistantTool)
            .where(models.VirtualAssistantTool.virtual_assistant_id == db_va.id)
        )
        # Add new associations from the payload
        if update_data["tools"]: # Ensure there are tools to process
            tool_associations_to_add = []
            for tool_info_data in update_data["tools"]: # tool_info_data is a dict here from model_dump
                                                        # or a ToolAssociationInfo object if not dumped yet
                # Ensure tool_info_data is treated as the Pydantic model or has the right keys
                tool_info = schemas.ToolAssociationInfo(**tool_info_data) if isinstance(tool_info_data, dict) else tool_info_data
                
                tool_associations_to_add.append(
                    models.VirtualAssistantTool(
                        virtual_assistant_id=db_va.id,
                        toolgroup_id=tool_info.toolgroup_id # Correctly use toolgroup_id
                    )
                )
            db.add_all(tool_associations_to_add)
    
    # The db_va object itself might have been modified if basic attributes were set
    db.add(db_va) # Add db_va to the session if it was modified directly

    try:
        await db.commit()
        await db.refresh(db_va) # Refresh to get any DB-generated changes and potentially updated relationships
        
        # Reload knowledge base associations
        kb_stmt = select(models.VirtualAssistantKnowledgeBase.vector_db_name).where(models.VirtualAssistantKnowledgeBase.virtual_assistant_id == db_va.id)
        kb_ids_result = await db.execute(kb_stmt)
        current_kb_ids = [row for row in kb_ids_result.scalars().all()]

        # Reload tool associations
        tool_stmt = select(models.VirtualAssistantTool.toolgroup_id).where(models.VirtualAssistantTool.virtual_assistant_id == db_va.id)
        tool_assoc_result = await db.execute(tool_stmt)
        current_tools_info = [
            schemas.ToolAssociationInfo(toolgroup_id=row)
            for row in tool_assoc_result.scalars().all()
        ]

    except HTTPException: # Re-raise HTTPExceptions if they occurred during K/B or Tool checks
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        # Log the exception 'e' for server-side debugging
        print(f"ERROR: update_virtual_assistant: {str(e)}") # Example logging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while updating the database: {str(e)}")

    # Construct and return the response using the refreshed data
    return schemas.VirtualAssistantRead(
        id=db_va.id,
        name=db_va.name,
        prompt=db_va.prompt,
        model_name=db_va.model_name,
        created_by=db_va.created_by,
        created_at=db_va.created_at,
        updated_at=db_va.updated_at,
        knowledge_base_ids=current_kb_ids,
        tools=current_tools_info
    )

@router.delete("/{va_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_virtual_assistant(va_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.VirtualAssistant).where(models.VirtualAssistant.id == va_id))
    db_va = result.scalar_one_or_none()
    if not db_va:
        raise HTTPException(status_code=404, detail="Virtual assistant not found")
    await db.delete(db_va)
    await db.commit()
    return None
