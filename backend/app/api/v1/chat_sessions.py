"""
Chat Sessions API endpoints for managing LlamaStack conversation sessions.

This module provides endpoints for creating, retrieving, and managing chat
sessions that are stored and managed by LlamaStack. Sessions track conversation state,
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
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.llamastack import (
    ERROR_NO_RESPONSE_MESSAGE,
    create_tool_call_trace_entry,
    get_client_from_request,
)
from ...crud.chat_sessions import chat_sessions
from ...crud.virtual_agents import virtual_agents
from ...database import get_db
from ...schemas.chat_sessions import (
    ChatSession,
    ConversationMessagesResponse,
    CreateSessionRequest,
    DeleteSessionResponse,
)
from . import attachments
from .users import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat_sessions", tags=["chat_sessions"])


def format_history_item(chunk: Any, text_parts: list, trace_entries: list) -> None:
    """
    Format conversation history items (direct data objects).

    Args:
        chunk: History item from LlamaStack conversation
        text_parts: List to accumulate text (modified in-place)
        trace_entries: List to accumulate trace entries (modified in-place)
    """
    # Log the chunk
    logger.info(f"format_history_item received: {chunk}")

    # Filter out items without type
    if not hasattr(chunk, "type"):
        return

    # Filter out tool discovery items
    if chunk.type == "mcp_list_tools":
        return

    # Handle message items
    if chunk.type == "message":
        if hasattr(chunk, "content") and chunk.content:
            for content_item in chunk.content:
                if hasattr(content_item, "type") and content_item.type in (
                    "input_text",
                    "output_text",
                ):
                    if hasattr(content_item, "text") and content_item.text:
                        text_parts.append(content_item.text)
                        logger.info(
                            f"Added text from message, text_parts now has {len(text_parts)} items"
                        )
        return

    # Handle MCP tool calls
    if chunk.type == "mcp_call":
        entry = create_tool_call_trace_entry(chunk)
        trace_entries.append(entry)
        logger.info(
            f"Added tool call entry, trace_entries now has {len(trace_entries)} items: {entry}"
        )
        return


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


def create_assistant_error_message(trace_entries: list) -> dict:
    """
    Create an assistant error message with trace entries attached.

    Used when the model executes tool calls but fails to generate a text response.
    Note: The frontend will add a ⚠️ emoji when displaying this error message.

    Args:
        trace_entries: List of trace entries (tool calls, reasoning) to attach

    Returns:
        Message dict with error content and trace entries
    """
    return {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": ERROR_NO_RESPONSE_MESSAGE}],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_entries": trace_entries,
    }


@router.get("/", response_model=List[ChatSession])
async def get_chat_sessions(
    agent_id: str,
    request: Request,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[ChatSession]:
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

        # Get sessions from database filtered by user
        local_sessions = await chat_sessions.get_by_agent(
            db, agent_id=agent_id, user_id=current_user.id, limit=limit
        )

        logger.info(
            f"Successfully retrieved {len(local_sessions)} sessions from local database"
        )

        # Convert local ChatSession objects to response format
        sessions_response = [
            ChatSession(
                id=session.id,
                title=session.title or f"Chat {str(session.id)[:8]}...",
                agent_id=session.agent_id,
                conversation_id=session.conversation_id,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
            )
            for session in local_sessions
        ]

        # Sort by created_at descending (newest first) to ensure
        # consistent ordering
        sessions_response.sort(key=lambda x: x.created_at or "", reverse=True)

        return sessions_response

    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ChatSession:
    """
    Get session metadata (messages are managed by LlamaStack Conversations API).

    Args:
        session_id: The unique identifier of the session to retrieve
        agent_id: The unique identifier of the agent that owns the session

    Returns:
        Session metadata including ID, title, agent_id, conversation_id, and timestamps

    Raises:
        HTTPException: If session is not found (404) or retrieval fails (500)
    """
    try:
        logger.info(f"Fetching session {session_id} for agent {agent_id}")

        # Get session from database (filtered by user)
        session = await chat_sessions.get_with_agent(
            db, session_id=session_id, user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        return ChatSession(
            id=session.id,
            title=session.title or f"Chat {str(session.id)[:8]}...",
            agent_id=session.agent_id,
            conversation_id=session.conversation_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chat session: {str(e)}"
        )


@router.get("/{session_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationMessagesResponse:
    """
    Get messages for a conversation from LlamaStack.

    Args:
        session_id: The unique identifier of the session

    Returns:
        List of messages from the LlamaStack conversation

    Raises:
        HTTPException: If session is not found (404) or retrieval fails (500)
    """
    try:
        logger.info(f"Fetching messages for session {session_id}")

        # Get session from database (filtered by user)
        session = await chat_sessions.get_with_agent(
            db, session_id=session_id, user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # If no conversation_id yet, return empty messages
        if not session.conversation_id:
            logger.info(
                f"No conversation_id for session {session_id}, returning empty messages"
            )
            return ConversationMessagesResponse(messages=[])

        # Fetch messages from LlamaStack
        client = get_client_from_request(request)
        try:
            # List items in the conversation
            # The include parameter is required (empty list to get default fields)
            # Available include values are for extra fields like:
            # "file_search_call.results", "reasoning.encrypted_content", etc.
            items_response = await client.conversations.items.list(
                conversation_id=session.conversation_id,
                after=None,
                include=[],
                limit=100,
                order="asc",
            )

            # Process conversation items using shared formatter
            messages = []
            pending_trace_entries = []

            logger.info(f"Total items received: {len(items_response.data)}")
            for item in items_response.data:
                # Process each item - extract text and trace info
                item_text_parts = []
                item_trace_entries = []
                format_history_item(item, item_text_parts, item_trace_entries)

                text = "".join(item_text_parts) if item_text_parts else None
                logger.info(
                    f"Formatter returned - text: {bool(text)}, trace_entries: {len(item_trace_entries)}"
                )

                # Collect trace entries
                if item_trace_entries:
                    pending_trace_entries.extend(item_trace_entries)
                    logger.info(
                        f"Extended pending_trace_entries, now has {len(pending_trace_entries)} items"
                    )

                # Process messages
                if text:
                    # If this is a user message and there are pending trace entries,
                    # create an assistant error message first to hold those trace entries
                    # (represents a failed assistant response with only tool calls)
                    if item.role == "user" and pending_trace_entries:
                        logger.info(
                            f"Creating assistant error message with {len(pending_trace_entries)} orphaned trace_entries"
                        )
                        assistant_error_msg = create_assistant_error_message(
                            pending_trace_entries
                        )
                        messages.append(assistant_error_msg)
                        pending_trace_entries = []

                    # Use appropriate content type based on role
                    content_type = (
                        "input_text" if item.role == "user" else "output_text"
                    )
                    message_dict = {
                        "type": "message",
                        "role": item.role,
                        "content": [{"type": content_type, "text": text}],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    # Attach pending trace entries to assistant messages
                    if item.role == "assistant" and pending_trace_entries:
                        message_dict["trace_entries"] = pending_trace_entries
                        logger.info(
                            f"Attached {len(pending_trace_entries)} trace_entries to assistant message"
                        )
                        pending_trace_entries = []

                    messages.append(message_dict)

            # Flush any remaining pending trace entries at the end
            # (happens when conversation ends with tool calls but no assistant response)
            if pending_trace_entries:
                logger.info(
                    f"Flushing {len(pending_trace_entries)} orphaned trace_entries at end of conversation"
                )
                final_assistant_error = create_assistant_error_message(
                    pending_trace_entries
                )
                messages.append(final_assistant_error)

            logger.info(
                f"Retrieved {len(messages)} messages for conversation {session.conversation_id}"
            )
            return ConversationMessagesResponse(messages=messages)

        except Exception as llamastack_error:
            logger.error(
                f"LlamaStack error retrieving conversation: {llamastack_error}"
            )
            # If conversation doesn't exist in LlamaStack, return empty messages
            return ConversationMessagesResponse(messages=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch conversation messages: {str(e)}"
        )


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_chat_session(
    session_id: str,
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DeleteSessionResponse:
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
        # Verify agent exists in our VirtualAgent table
        agent_config = await virtual_agents.get(db, id=agent_id)
        if not agent_config:
            logger.error(f"Agent {agent_id} not found in VirtualAgent")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Delete session and related data (only if user owns it)
        deleted = await chat_sessions.delete_session(
            db, session_id=session_id, user_id=current_user.id
        )

        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Clean up attachments (non-critical, don't fail if this fails)
        try:
            attachments.delete_attachments_for_session(session_id)
            logger.info(f"Successfully deleted session {session_id} and attachments")
        except Exception as attachment_error:
            logger.warning(
                f"Failed to delete attachments for session {session_id}: "
                f"{attachment_error}"
            )
            logger.info(
                f"Successfully deleted session {session_id} "
                f"(attachments cleanup failed)"
            )

        return DeleteSessionResponse(
            message=f"Session {session_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chat session: {str(e)}"
        )


@router.post("/", response_model=ChatSession)
async def create_chat_session(
    sessionRequest: CreateSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ChatSession:
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
        # Verify agent exists in our VirtualAgent table
        agent_config = await virtual_agents.get(db, id=sessionRequest.agent_id)
        if not agent_config:
            logger.error(f"Agent {sessionRequest.agent_id} not found in VirtualAgent")
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

        # Create session locally (conversation will be created by LlamaStack on first message)
        session_id = uuid.uuid4()
        logger.info(f"Generated local session ID: {session_id}")

        # Create ChatSession record in database
        session_data = {
            "id": session_id,
            "title": session_name,
            "agent_id": sessionRequest.agent_id,
            "user_id": current_user.id,
            "conversation_id": None,  # Will be set when first message is sent
        }

        new_session = await chat_sessions.create_session(db, session_data=session_data)

        logger.info(f"Created ChatSession record for {session_id}")

        return ChatSession(
            id=session_id,
            title=session_name,
            agent_id=sessionRequest.agent_id,
            conversation_id=None,
            created_at=new_session.created_at.isoformat(),
            updated_at=new_session.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {str(e)}"
        )
