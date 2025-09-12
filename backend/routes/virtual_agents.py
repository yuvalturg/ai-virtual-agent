"""
Virtual Agents API endpoints using LlamaStack's Responses API.

This module provides CRUD operations for virtual agents using LlamaStack's
Responses API instead of the deprecated Agents API. Virtual agents (personas)
are now implemented using the more flexible Responses API which offers:
- Dynamic per-call configuration
- OpenAI-compatible tool patterns
- Conversation branching capabilities
"""

import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..api.llamastack import get_client_from_request
from ..database import get_db
from ..routes import attachments

logger = logging.getLogger(__name__)

# Feature flag for auto-assignment of agents to users
AUTO_ASSIGN_AGENTS_TO_USERS = (
    os.getenv("AUTO_ASSIGN_AGENTS_TO_USERS", "true").lower() == "true"
)

router = APIRouter(prefix="/virtual_agents", tags=["virtual_agents"])


async def validate_and_get_vector_store_ids(
    knowledge_base_ids: List[str], request: Request
) -> List[str]:
    """
    Validate that knowledge bases exist in LlamaStack and return their vector store IDs.

    Args:
        knowledge_base_ids: List of knowledge base names to validate
        request: FastAPI request object for LlamaStack client access

    Returns:
        List of corresponding vector store IDs

    Raises:
        HTTPException: If any knowledge bases are not found in LlamaStack
    """
    if not knowledge_base_ids:
        return []

    try:
        client = get_client_from_request(request)
        vector_stores = await client.vector_stores.list()
        vs_name_to_id = {vs.name: vs.id for vs in vector_stores.data}

        # Check that all knowledge bases exist in LlamaStack
        vector_store_ids = []
        missing_kbs = []

        for kb_name in knowledge_base_ids:
            if kb_name in vs_name_to_id:
                vector_store_ids.append(vs_name_to_id[kb_name])
            else:
                missing_kbs.append(kb_name)

        if missing_kbs:
            raise HTTPException(
                status_code=400,
                detail=f"Knowledge bases not found in LlamaStack: {missing_kbs}",
            )

        return vector_store_ids

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate knowledge bases in LlamaStack: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to validate knowledge bases with LlamaStack"
        )


async def sync_all_users_with_all_agents(db: AsyncSession) -> dict:
    """
    Utility function to ensure all existing users have access to all existing agents.

    This function is useful for fixing any inconsistencies in agent assignments
    and ensuring that all users can access all available agents.

    The behavior can be disabled by setting AUTO_ASSIGN_AGENTS_TO_USERS=false

    Args:
        db: Database session

    Returns:
        Dict with sync results including counts of users and agents processed
    """
    # Check if auto-assignment is enabled
    if not AUTO_ASSIGN_AGENTS_TO_USERS:
        logger.info("Auto-assignment of agents to users is disabled")
        return {"status": "disabled", "users_processed": 0, "agents_processed": 0}

    try:
        # Get all users
        users_result = await db.execute(select(models.User))
        all_users = users_result.scalars().all()

        # Get all agent IDs
        agents_result = await db.execute(select(models.VirtualAgentConfig.id))
        all_agent_ids = [row[0] for row in agents_result.all()]

        # Set each user's agent_ids to the complete list of all agents
        for user in all_users:
            user.agent_ids = all_agent_ids

        await db.commit()

        result = {
            "users_processed": len(all_users),
            "total_agents": len(all_agent_ids),
            "success": True,
        }

        logger.info(f"Sync completed: {result}")
        return result

    except Exception as e:
        await db.rollback()
        logger.error(f"Error syncing users with agents: {str(e)}")
        return {
            "users_processed": 0,
            "total_agents": 0,
            "success": False,
            "error": str(e),
        }


async def get_virtual_agent_config(
    db: AsyncSession, agent_id: str
) -> Optional[models.VirtualAgentConfig]:
    """
    Utility function to get virtual agent configuration by ID.

    Args:
        db: Database session
        agent_id: The unique identifier of the virtual agent

    Returns:
        VirtualAgentConfig object or None if not found
    """
    try:
        result = await db.execute(
            select(models.VirtualAgentConfig).where(
                models.VirtualAgentConfig.id == agent_id
            )
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error retrieving virtual agent config {agent_id}: {str(e)}")
        return None


def get_strategy(sampling_strategy, temperature, top_p, top_k):
    """
    Determines the sampling strategy for the LLM based on user selection.
    Args:
        sampling_strategy: 'greedy', 'top-p', or 'top-k'
        temperature: Temperature parameter for sampling
        top_p: Top-p parameter for nucleus sampling
        top_k: Top-k parameter for k sampling
    Returns:
        Dict containing the sampling strategy configuration
    """
    if sampling_strategy == "top-p":
        temp = max(temperature, 0.1)  # Ensure temp doesn't become 0
        return {"type": "top_p", "temperature": temperature, "top_p": top_p}
    elif sampling_strategy == "top-k":
        temp = max(temperature, 0.1)  # Ensure temp doesn't become 0
        return {"type": "top_k", "temperature": temp, "top_k": top_k}
    # Default and 'greedy' case
    return {"type": "greedy"}


def config_to_response(config: models.VirtualAgentConfig) -> schemas.VirtualAgentRead:
    """
    Convert a VirtualAgentConfig database model to API response format.

    Args:
        config: VirtualAgentConfig database model

    Returns:
        VirtualAgentRead schema with formatted data
    """
    # Convert tools back to expected format
    tools = []
    if config.tools:
        for tool in config.tools:
            if isinstance(tool, dict):
                tools.append(
                    schemas.ToolAssociationInfo(
                        toolgroup_id=tool.get("toolgroup_id", str(tool))
                    )
                )
            else:
                tools.append(schemas.ToolAssociationInfo(toolgroup_id=str(tool)))

    return schemas.VirtualAgentRead(
        id=config.id,
        name=config.name,
        input_shields=config.input_shields or [],
        output_shields=config.output_shields or [],
        prompt=config.prompt,
        model_name=config.model_name,
        knowledge_base_ids=config.knowledge_base_ids or [],
        tools=tools,
    )


@router.post(
    "/",
    response_model=schemas.VirtualAgentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_virtual_agent(
    va: schemas.VirtualAgentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new virtual agent configuration for use with Responses API.

    Since the Responses API doesn't create persistent agents, we store the
    virtual agent configuration in our database and use it when creating responses.

    Args:
        va: Virtual agent configuration including model, tools, and settings

    Returns:
        The created virtual agent configuration with generated ID

    Raises:
        HTTPException: If creation fails
    """
    try:
        # Generate a unique ID for this virtual agent configuration
        agent_id = str(uuid.uuid4())

        # Store the virtual agent configuration in the new VirtualAgentConfig table
        try:
            # Validate knowledge bases and get vector store IDs if needed
            vector_store_ids = []
            if va.knowledge_base_ids:
                vector_store_ids = await validate_and_get_vector_store_ids(
                    va.knowledge_base_ids, request
                )

            # Create VirtualAgentConfig record
            config = models.VirtualAgentConfig(
                id=agent_id,
                name=va.name,
                model_name=va.model_name,
                prompt=va.prompt,
                tools=[
                    (
                        tool.dict()
                        if hasattr(tool, "dict")
                        else tool.__dict__ if hasattr(tool, "__dict__") else str(tool)
                    )
                    for tool in (va.tools or [])
                ],
                knowledge_base_ids=va.knowledge_base_ids or [],
                vector_store_ids=vector_store_ids,
                input_shields=va.input_shields or [],
                output_shields=va.output_shields or [],
                sampling_strategy=getattr(va, "sampling_strategy", None),
                temperature=getattr(va, "temperature", None),
                top_p=getattr(va, "top_p", None),
                top_k=getattr(va, "top_k", None),
                max_tokens=getattr(va, "max_tokens", None),
                repetition_penalty=getattr(va, "repetition_penalty", None),
                max_infer_iters=getattr(va, "max_infer_iters", None),
            )

            db.add(config)
            await db.commit()
            logger.info(f"Stored virtual agent configuration: {agent_id}")

        except Exception as db_error:
            logger.error(f"Error storing virtual agent config: {str(db_error)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store virtual agent configuration: {str(db_error)}",
            )

        logger.info(f"Created virtual agent configuration: {agent_id} for {va.name}")

        # Sync all users with all agents (including the new one)
        try:
            sync_result = await sync_all_users_with_all_agents(db)
            logger.info(f"Agent-user sync completed: {sync_result}")
        except Exception as sync_error:
            logger.error(f"Error syncing users with agents: {str(sync_error)}")
            # Don't fail the agent creation if sync fails

        # Return the virtual agent configuration (without agent_type)
        return schemas.VirtualAgentRead(
            id=agent_id,
            name=va.name,
            input_shields=va.input_shields,
            output_shields=va.output_shields,
            prompt=va.prompt,
            model_name=va.model_name,
            knowledge_base_ids=va.knowledge_base_ids,
            tools=va.tools,
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"ERROR: create_virtual_agent: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/", response_model=List[schemas.VirtualAgentRead])
async def get_virtual_agents(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all virtual agent configurations from database.

    Returns:
        List of all virtual agent configurations stored in the system
    """
    try:
        result = await db.execute(select(models.VirtualAgentConfig))
        configs = result.scalars().all()

        response_list = []
        for config in configs:
            response_list.append(config_to_response(config))

        return response_list

    except Exception as e:
        logger.error(f"Error retrieving virtual agents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{va_id}", response_model=schemas.VirtualAgentRead)
async def read_virtual_agent(va_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific virtual agent configuration by ID.

    Args:
        va_id: The unique identifier of the virtual agent

    Returns:
        The virtual agent configuration

    Raises:
        HTTPException: If virtual agent not found
    """
    try:
        config = await get_virtual_agent_config(db, va_id)

        if not config:
            raise HTTPException(
                status_code=404, detail=f"Virtual agent {va_id} not found"
            )

        return config_to_response(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving virtual agent {va_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


# @router.put("/{va_id}", response_model=schemas.VirtualAgentRead)
# async def update_virtual_agent(va_id: str):
#     pass


@router.delete("/{va_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_virtual_agent(va_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a virtual agent configuration from the database.

    Args:
        va_id: The unique identifier of the virtual agent to delete

    Returns:
        None (204 No Content status)
    """
    try:
        # First check if the agent exists
        check_result = await db.execute(
            select(models.VirtualAgentConfig).where(
                models.VirtualAgentConfig.id == va_id
            )
        )
        if not check_result.scalar_one_or_none():
            raise HTTPException(
                status_code=404, detail=f"Virtual agent {va_id} not found"
            )

        # Delete all sessions associated with this agent
        sessions_result = await db.execute(
            select(models.ChatSession).where(
                text("session_state->>'agent_id' = :agent_id")
            ),
            {"agent_id": va_id},
        )
        sessions_to_delete = sessions_result.scalars().all()

        # Clean up attachments for each session
        for session in sessions_to_delete:
            try:
                attachments.delete_attachments_for_session(session.id)
                logger.info(f"Deleted attachments for session {session.id}")
            except Exception as attachment_error:
                logger.warning(
                    f"Failed to delete attachments for session {session.id}: "
                    f"{attachment_error}"
                )

        # Delete all sessions for this agent
        if sessions_to_delete:
            await db.execute(
                delete(models.ChatSession).where(
                    text("session_state->>'agent_id' = :agent_id")
                ),
                {"agent_id": va_id},
            )
            logger.info(f"Deleted {len(sessions_to_delete)} sessions for agent {va_id}")

        # Delete from VirtualAgentConfig table
        await db.execute(
            delete(models.VirtualAgentConfig).where(
                models.VirtualAgentConfig.id == va_id
            )
        )

        await db.commit()
        logger.info(f"Successfully deleted virtual agent {va_id}")

        # Sync all users with remaining agents (removes deleted agent from all users)
        try:
            sync_result = await sync_all_users_with_all_agents(db)
            logger.info(f"Agent-user sync completed after deletion: {sync_result}")
        except Exception as sync_error:
            logger.error(
                f"Error syncing users with agents after deletion: {str(sync_error)}"
            )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete agent {va_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete virtual agent: {str(e)}"
        )

    return None


@router.post("/sync-users-agents")
async def sync_users_with_agents(
    db: AsyncSession = Depends(get_db),
):
    """
    Sync all existing users with all existing agents.

    This endpoint ensures that all users have access to all available agents.
    Useful for fixing any inconsistencies in agent assignments or for ensuring
    that all users can see newly created agents.

    Returns:
        Dict with sync results including counts of users and agents processed
    """
    try:
        result = await sync_all_users_with_all_agents(db)
        return result
    except Exception as e:
        logger.error(f"Error in sync endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to sync users with agents: {str(e)}"
        )
