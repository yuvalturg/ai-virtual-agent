"""
Chat Sessions API endpoints for managing LlamaStack conversation sessions.

This module provides endpoints for creating, retrieving, and managing chat
sessions
that are stored and managed by LlamaStack. Sessions track conversation state,
message history, and agent context for continuous conversations.

Key Features:
- Create new chat sessions with specific agents
- Retrieve session lists filtered by agent
- Get detailed session information including message history
- Delete chat sessions
- Automatic session metadata extraction from LlamaStack

All session data is managed by LlamaStack's session API, providing persistent
conversation state across multiple interactions.
"""

import logging
import random
import string
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..api.llamastack import get_client_from_request
from ..database import get_db
from ..routes import attachments
from .virtual_agents import get_virtual_agent_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat_sessions", tags=["chat_sessions"])


def convert_internal_urls_to_relative(message_data: dict) -> None:
    """
    Convert internal service URLs back to relative URLs for frontend consumption.

    Args:
        message_data: Message data dict (modified in-place)
    """
    from urllib.parse import urlparse

    for content_item in message_data.get("content", []):
        if content_item.get("type") == "input_image":
            if image_url := content_item.get("image_url", ""):
                parsed = urlparse(image_url)
                # Keep only the path part of the URL
                content_item["image_url"] = parsed.path


class CreateSessionRequest(BaseModel):
    """
    Request model for creating new chat sessions.

    Attributes:
        agent_id: The unique identifier of the agent to create a session for
        session_name: Optional custom name for the session. If not provided,
                     a unique name will be generated automatically
    """

    agent_id: str
    session_name: Optional[str] = None


@router.get("/")
async def get_chat_sessions(
    agent_id: str, request: Request, limit: int = 50, db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Get a list of chat sessions for a specific agent from LlamaStack.

    Retrieves session metadata including session IDs, titles, agent
    information, and timestamps. Sessions are sorted by creation date
    (newest first) and limited to the specified number of results.

    Args:
        agent_id: The unique identifier of the agent to retrieve sessions for
        limit: Maximum number of sessions to return (default: 50)

    Returns:
        List of session summary dictionaries containing:
        - id: Session identifier
        - title: Session display title
        - agent_name: Display name of the associated agent
        - created_at: Session creation timestamp
        - updated_at: Session last update timestamp

    Raises:
        HTTPException: If session retrieval fails or agent is not found
    """
    try:
        logger.info(f"Attempting to list sessions for agent {agent_id}")

        # Use our local ChatSession table instead of LlamaStack agents API

        # Use JSON path extraction to check for agent_id
        result = await db.execute(
            select(models.ChatSession)
            .where(text("session_state->>'agent_id' = :agent_id"))
            .order_by(models.ChatSession.updated_at.desc()),
            {"agent_id": agent_id},
        )
        local_sessions = result.scalars().all()

        logger.info(
            f"Successfully retrieved {len(local_sessions)} sessions from local database"
        )

        # Get agent name from our VirtualAgentConfig instead of LlamaStack
        agent_name = "Unknown Agent"
        try:
            result = await db.execute(
                select(models.VirtualAgentConfig).where(
                    models.VirtualAgentConfig.id == agent_id
                )
            )
            agent_config = result.scalar_one_or_none()
            if agent_config:
                agent_name = agent_config.name
        except Exception as e:
            logger.warning(f"Could not get agent info: {e}")

        # Convert local ChatSession objects to response format
        sessions_response = [
            {
                "id": session.id,
                "title": session.title or f"Chat {session.id[:8]}...",
                "agent_name": session.agent_name or agent_name,
                "created_at": (
                    session.created_at.isoformat() if session.created_at else None
                ),
                "updated_at": (
                    session.updated_at.isoformat() if session.updated_at else None
                ),
                "last_response_id": (
                    session.session_state.get("last_response_id")
                    if session.session_state
                    else None
                ),
            }
            for session in local_sessions[:limit]
        ]

        # Sort by created_at descending (newest first) to ensure
        # consistent ordering
        sessions_response.sort(key=lambda x: x.get("created_at") or "", reverse=True)

        return sessions_response

    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}"
        )


def get_agent_display_name(agent) -> str:
    """
    Extract a display-friendly name from a LlamaStack agent object.

    This helper function attempts to extract a meaningful display name from
    various agent object formats returned by LlamaStack, with fallback options.

    Args:
        agent: LlamaStack agent object with varying structure

    Returns:
        str: A display-friendly agent name, defaults to "Unknown Agent" if
             no name found
    """
    if hasattr(agent, "agent_config") and isinstance(agent.agent_config, dict):
        return agent.agent_config.get("name", "Unknown Agent")
    elif hasattr(agent, "name"):
        return agent.name
    elif hasattr(agent, "instructions"):
        instructions = str(agent.instructions)
        return (instructions[:50] + "...") if len(instructions) > 50 else instructions
    return "Unknown Agent"


@router.get("/{session_id}")
async def get_chat_session(
    session_id: str,
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
    load_messages: bool = True,
) -> dict:
    """
    Get detailed information for a specific chat session including message
    history.

    Retrieves the complete session data from LlamaStack including all
    conversation
    turns (user messages and assistant responses). If session retrieval fails,
    returns a basic session structure with empty message history.

    Args:
        session_id: The unique identifier of the session to retrieve
        agent_id: The unique identifier of the agent that owns the session

    Returns:
        Dictionary containing complete session details:
        - id: Session identifier
        - title: Session display title
        - agent_name: Display name of the associated agent
        - agent_id: Agent identifier
        - messages: List of conversation messages with role and content
        - created_at: Session creation timestamp
        - updated_at: Session last update timestamp

    Raises:
        HTTPException: If agent is not found (404) or retrieval fails (500)
    """
    try:
        logger.info(f"Fetching session {session_id} for agent {agent_id}")

        # Verify agent exists in our VirtualAgentConfig table instead of LlamaStack
        agent_config = await get_virtual_agent_config(db, agent_id)
        if not agent_config:
            logger.error(f"Agent {agent_id} not found in VirtualAgentConfig")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # With Responses API, we don't have persistent sessions in LlamaStack
        # Session history would need to be managed differently or stored locally
        # For now, return empty session structure

        # Get agent name from our VirtualAgentConfig
        agent_name = agent_config.name if agent_config.name else "Unknown Agent"

        logger.info(
            f"Returning session structure for {session_id} "
            f"(Responses API doesn't store session history)"
        )

        # Try to get session from database to retrieve state
        result = await db.execute(
            select(models.ChatSession).where(models.ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        # Get last_response_id from session state if available
        last_response_id = None
        if session and session.session_state:
            last_response_id = session.session_state.get("last_response_id")

        # Get messages from LlamaStack responses API
        messages = []
        total_messages = 0
        has_more = False

        if session and load_messages and last_response_id:
            # Use LlamaStack responses.list() API to find the conversation history
            logger.info(
                f"Fetching messages for session {session_id}, agent {agent_id}, "
                f"last_response_id: {last_response_id}, page: {page}, "
                f"page_size: {page_size}"
            )
            try:
                client = get_client_from_request(request)

                # List responses with some optimization - limit results and filter
                # by model if possible
                agent_config = await get_virtual_agent_config(db, agent_id)
                list_params = {
                    "limit": 100,  # Reasonable limit to avoid huge responses
                    "order": "desc",  # Newest first
                }
                if agent_config and agent_config.model_name:
                    list_params["model"] = agent_config.model_name

                responses_list = await client.responses.list(**list_params)

                # Find the response with our target ID
                target_response = None
                logger.info(f"Looking for response ID: {last_response_id}")
                logger.info(f"Found {len(responses_list.data)} responses in list")

                for i, resp in enumerate(responses_list.data):
                    logger.info(f"Response {i}: {resp.id}")
                    if resp.id == last_response_id:
                        target_response = resp
                        logger.info(f"Found target response at index {i}")
                        break

                if not target_response:
                    logger.warning(
                        f"Target response {last_response_id} not found in list"
                    )

                def should_include_message(
                    msg_data: dict, message_source: str = ""
                ) -> bool:
                    """
                    Filter out tool call messages and other non-conversation messages.
                    Returns True if message should be included, False if it should be skipped.
                    """
                    if not msg_data.get("role") or not msg_data.get("content"):
                        msg_type = msg_data.get("type", "unknown")
                        msg_info = str(msg_data)
                        if msg_type == "mcp_list_tools":
                            tools_list = [x["name"] for x in msg_data["tools"]]
                            msg_info = f"server_label={msg_data['server_label']}, tools={tools_list}"
                        elif msg_type == "mcp_call":
                            msg_info = (
                                f"server_label={msg_data['server_label']}, "
                                f"name={msg_data['name']}, arguments={msg_data['arguments']}"
                            )
                        source_info = f" {message_source}" if message_source else ""
                        logger.info(
                            f"Skipping{source_info} message without role/content: "
                            f"{msg_type=} {msg_info}"
                        )
                        return False
                    return True

                if (
                    target_response
                    and hasattr(target_response, "input")
                    and target_response.input
                ):
                    # Convert LlamaStack message format to our API format
                    all_messages = []

                    # Process input messages (conversation history) - serialize
                    # entire message
                    for i, llamastack_msg in enumerate(target_response.input):
                        msg_data = llamastack_msg.model_dump()

                        if not should_include_message(msg_data, "input"):
                            continue

                        convert_internal_urls_to_relative(msg_data)
                        all_messages.append(msg_data)

                    # Add the final output message - serialize entire message
                    if hasattr(target_response, "output") and target_response.output:
                        for i, output_msg in enumerate(target_response.output):
                            msg_data = output_msg.model_dump()

                            if not should_include_message(msg_data, "output"):
                                continue

                            convert_internal_urls_to_relative(msg_data)
                            all_messages.append(msg_data)

                    total_messages = len(all_messages)

                    # Apply pagination
                    offset = (page - 1) * page_size
                    has_more = offset + page_size < total_messages
                    messages = all_messages[offset : offset + page_size]

                    logger.info(
                        f"Successfully fetched {len(messages)} messages for "
                        f"session {session_id} (total: {total_messages}, page: {page}, "
                        f"has_more: {has_more})"
                    )

            except Exception as e:
                logger.warning(f"Could not retrieve messages from LlamaStack: {e}")
                # Fall back to empty messages
        else:
            logger.info(
                f"Not fetching messages for session {session_id}: "
                f"session={session is not None}, load_messages={load_messages}, "
                f"last_response_id={last_response_id}"
            )

        return {
            "id": session_id,
            "title": session.title if session else f"Chat {session_id[:8]}...",
            "agent_name": agent_name,
            "agent_id": agent_id,
            "messages": messages,
            "created_at": (
                session.created_at.isoformat()
                if session
                else datetime.now().isoformat()
            ),
            "updated_at": (
                session.updated_at.isoformat()
                if session
                else datetime.now().isoformat()
            ),
            "last_response_id": last_response_id,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_messages": total_messages,
                "has_more": has_more,
                "messages_loaded": len(messages),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chat session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_chat_session(
    session_id: str, agent_id: str, request: Request, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a chat session from LlamaStack.

    Permanently removes the specified chat session and all associated
    conversation history from LlamaStack. This operation cannot be undone.

    Args:
        session_id: The unique identifier of the session to delete
        agent_id: The unique identifier of the agent that owns the session

    Returns:
        Dictionary containing the result of the delete operation from
        LlamaStack

    Raises:
        HTTPException: If agent is not found (404) or deletion fails (500)
    """
    try:
        # Verify agent exists in our VirtualAgentConfig table
        agent_config = await get_virtual_agent_config(db, agent_id)
        if not agent_config:
            logger.error(f"Agent {agent_id} not found in VirtualAgentConfig")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # With Responses API, we don't have persistent sessions in LlamaStack
        # Just clean up local session metadata and attachments
        try:
            # Delete from our local ChatSession table if it exists
            await db.execute(
                delete(models.ChatSession).where(models.ChatSession.id == session_id)
            )
            await db.commit()

            # Clean up attachments (non-critical, don't fail if this fails)
            try:
                attachments.delete_attachments_for_session(session_id)
                logger.info(
                    f"Successfully deleted session {session_id} and attachments"
                )
            except Exception as attachment_error:
                logger.warning(
                    f"Failed to delete attachments for session {session_id}: "
                    f"{attachment_error}"
                )
                logger.info(
                    f"Successfully deleted session {session_id} "
                    f"(attachments cleanup failed)"
                )

            return {"message": f"Session {session_id} deleted successfully"}

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting session: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chat session: {str(e)}"
        )


@router.post("/")
async def create_chat_session(
    sessionRequest: CreateSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new chat session for an agent using LlamaStack.

    Creates a new conversation session associated with a specific agent. If no
    session name is provided, generates a unique name with timestamp and random
    component. The session is immediately available for chat interactions.

    Args:
        request: CreateSessionRequest containing:
            - agent_id: The unique identifier of the agent
            - session_name: Optional custom name for the session

    Returns:
        Dictionary containing the created session details:
        - id: Generated session identifier
        - title: Session name/title
        - agent_name: Display name of the associated agent
        - agent_id: Agent identifier
        - messages: Empty list (new session)
        - created_at: Session creation timestamp
        - updated_at: Session creation timestamp

    Raises:
        HTTPException: If agent is not found (404) or session creation
                       fails (500)
    """
    try:
        # Verify agent exists in our VirtualAgentConfig table instead of LlamaStack
        result = await db.execute(
            select(models.VirtualAgentConfig).where(
                models.VirtualAgentConfig.id == sessionRequest.agent_id
            )
        )
        agent_config = result.scalar_one_or_none()
        if not agent_config:
            logger.error(
                f"Agent {sessionRequest.agent_id} not found in VirtualAgentConfig"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Agent {sessionRequest.agent_id} not found",
            )
        logger.info(f"Found agent config: {agent_config.id}")

        # Generate unique session name
        if sessionRequest.session_name:
            session_name = sessionRequest.session_name
        else:
            # Generate unique name with timestamp and random component
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            random_suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=4)
            )
            session_name = f"Chat-{timestamp}-{random_suffix}"
        # Create session locally without LlamaStack
        session_id = str(uuid.uuid4())
        logger.info(f"Generated local session ID: {session_id}")

        # Get agent name for display from our VirtualAgentConfig
        agent_name = agent_config.name if agent_config else "Unknown Agent"

        # Create ChatSession record in database
        new_session = models.ChatSession(
            id=session_id,
            title=session_name,  # Use the provided session name
            agent_name=agent_name,
            session_state={
                "agent_id": sessionRequest.agent_id,
                "last_response_id": None,  # No responses yet
            },
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        logger.info(f"Created ChatSession record for {session_id}")

        return {
            "id": session_id,
            "title": session_name,
            "agent_name": agent_name,
            "agent_id": sessionRequest.agent_id,
            "messages": [],
            "created_at": new_session.created_at.isoformat(),
            "updated_at": new_session.updated_at.isoformat(),
            "last_response_id": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {str(e)}"
        )


@router.get("/debug/{agent_id}")
async def debug_session_listing(agent_id: str, request: Request):
    """
    Debug endpoint for troubleshooting session listing functionality.

    This development/debugging endpoint provides detailed information about
    session listing operations, including agent verification, session resource
    inspection, and method execution results. Used for diagnosing issues
    with LlamaStack session API interactions.

    Args:
        agent_id: The unique identifier of the agent to debug

    Returns:
        Dictionary containing debug information:
        - agent_id: The agent being debugged
        - response_type: Type of response from LlamaStack
        - response_value: Raw response value
        - sessions_count: Number of sessions found
        - sessions: List of session data
        - error: Error message if operation fails

    Note:
        This endpoint should only be used for development and debugging
        purposes.
    """
    try:
        logger.info(f"=== DEBUG SESSION LISTING FOR AGENT {agent_id} ===")

        # Test 1: Check if agent exists
        client = get_client_from_request(request)
        try:
            agent = await client.agents.retrieve(agent_id=agent_id)
            logger.info(f"✅ Agent exists: {agent.agent_id}")
        except Exception as e:
            logger.error(f"❌ Agent not found: {e}")
            return {"error": f"Agent not found: {e}"}

        # Test 2: Check session resource type
        session_resource = client.agents.session
        logger.info(f"Session resource type: {type(session_resource)}")
        logger.info(
            "Session resource methods: "
            f"{[m for m in dir(session_resource) if not m.startswith('_')]}"
        )

        # Test 3: Try to call list method
        try:
            sessions_response = await client.agents.session.list(agent_id=agent_id)
            logger.info("✅ List method called successfully")
            logger.info(f"Response type: {type(sessions_response)}")
            logger.info(f"Response value: {sessions_response}")
            logger.info(f"Response dir: {dir(sessions_response)}")

            # Try to extract sessions
            if hasattr(sessions_response, "sessions"):
                sessions = sessions_response.sessions
                logger.info(f"Found sessions attr: {sessions}")
            elif isinstance(sessions_response, list):
                sessions = sessions_response
                logger.info(f"Response is direct list: {sessions}")
            else:
                sessions = []
                logger.info("No sessions found in response")

            return {
                "agent_id": agent_id,
                "response_type": str(type(sessions_response)),
                "response_value": str(sessions_response),
                "sessions_count": len(sessions) if sessions else 0,
                "sessions": sessions if sessions else [],
            }

        except Exception as e:
            logger.error(f"❌ List method failed: {e}")
            logger.error(f"Exception type: {type(e)}")
            return {"error": f"List method failed: {e}"}

    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        return {"error": f"Debug failed: {e}"}
