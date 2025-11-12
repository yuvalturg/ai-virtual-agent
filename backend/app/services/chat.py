"""
Chat service for handling LlamaStack conversations with virtual agent configurations.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.llamastack import get_client_from_request
from ..models import ChatSession

logger = logging.getLogger(__name__)


def expand_image_url(content_item: Dict[str, Any]) -> None:
    """
    Expand relative image URL to full URL for LlamaStack inference service.

    Args:
        content_item: Content item that may contain a relative image URL
                     (modified in-place)
    """
    if content_item.get("type") == "input_image" and content_item.get("image_url"):
        image_url = content_item["image_url"]
        if image_url.startswith("/"):
            attachments_endpoint = os.getenv(
                "ATTACHMENTS_INTERNAL_API_ENDPOINT", "http://ai-virtual-agent:8000"
            )
            content_item["image_url"] = f"{attachments_endpoint}{image_url}"


async def build_responses_tools(
    tools: Optional[List[Any]],
    vector_store_ids: Optional[List[str]],
    request: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Convert virtual agent tools to OpenAI Responses API compatible format.

    The Responses API uses OpenAI-compatible tool patterns:
    - file_search for RAG/knowledge base queries
    - web_search for web searches
    - code_interpreter for code execution

    Args:
        tools: List of virtual agent tools to convert
        vector_store_ids: List of LlamaStack vector store IDs for file_search tools

    Returns:
        List of tools in OpenAI Responses API format
    """
    responses_tools = []

    if not tools:
        return responses_tools

    for tool_info in tools:
        tool_id = tool_info["toolgroup_id"]

        # Convert to OpenAI Responses API tool format
        if tool_id == "builtin::rag":
            if vector_store_ids:
                responses_tools.append(
                    {"type": "file_search", "vector_store_ids": vector_store_ids}
                )
        elif "web_search" in tool_id or "search" in tool_id:
            responses_tools.append({"type": "web_search"})
        elif tool_id.startswith("mcp::"):
            # For MCP tools, we need to get server info from LlamaStack
            if request:
                try:
                    client = get_client_from_request(request)
                    # Get all toolgroups to find the one matching our tool
                    toolgroups = await client.toolgroups.list()
                    for toolgroup in toolgroups:
                        if str(toolgroup.identifier) == tool_id:
                            responses_tools.append(
                                {
                                    "type": "mcp",
                                    "server_label": toolgroup.args.get(
                                        "name", str(toolgroup.identifier)
                                    ),
                                    "server_url": toolgroup.mcp_endpoint.uri,
                                }
                            )
                            break
                except Exception as e:
                    logger.warning(f"Failed to get MCP server info for {tool_id}: {e}")
                    # Fallback: skip this tool if we can't get server info
            else:
                logger.warning(
                    f"Cannot get MCP server info for {tool_id} without request object"
                )
        else:
            # For other tools, try to use the toolgroup_id directly
            responses_tools.append({"type": tool_id})

    return responses_tools


class ChatService:
    """
    A chat service using LlamaStack's Responses API with virtual agent configurations.

    This approach:
    - Uses virtual agent configs as templates for model/tools/prompt
    - Dynamically passes model and tools from config to each Responses API call
    - Sends full conversation history for proper context
    - No need to pre-create persistent agents

    Args:
        request: FastAPI request object for LlamaStack client access
        db: Database session for accessing virtual agent configurations
        user_id: ID of the authenticated user
    """

    def __init__(self, request: Request, db: AsyncSession, user_id):
        self.request = request
        self.db = db
        self.user_id = user_id  # Can be UUID or string, SQLAlchemy handles conversion

    async def _get_or_create_conversation(self, session_id: str, client) -> str:
        """
        Get or create a LlamaStack conversation for the session.

        Args:
            session_id: Chat session ID
            client: LlamaStack client

        Returns:
            LlamaStack conversation ID
        """
        # Get session from database
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise Exception(f"Session {session_id} not found")

        # Return existing conversation_id if available
        if session.conversation_id:
            logger.info(f"Using existing conversation: {session.conversation_id}")
            return session.conversation_id

        # Create new conversation in LlamaStack
        conversation = await client.conversations.create()
        conversation_id = conversation.id

        # Store conversation_id in our session
        session.conversation_id = conversation_id
        await self.db.commit()
        logger.info(f"Created new conversation: {conversation_id}")

        return conversation_id

    async def _prepare_conversation_input(self, user_input):
        """
        Prepare input with just the current user message.

        When using the conversation parameter, LlamaStack manages the conversation
        history automatically - we only need to send the new user message.
        """
        # Prepare current user input only
        if isinstance(user_input, list):
            # Multimodal content - serialize and expand URLs
            content_items = []
            for item in user_input:
                content_item = item.model_dump()
                expand_image_url(content_item)
                content_items.append(content_item)
            return [{"role": "user", "content": content_items}]
        else:
            # Single content item
            content_item = user_input.model_dump()
            expand_image_url(content_item)
            return [{"role": "user", "content": [content_item]}]

    async def _update_session_title(
        self,
        agent_id: str,
        session_id: str,
        user_input: Any,
    ) -> None:
        """
        Update session title based on first user message.

        Args:
            agent_id: Virtual agent configuration ID
            session_id: Chat session ID
            user_input: User message content
        """
        # Get session
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == self.user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            # Session should already exist (created via create_chat_session endpoint)
            logger.warning(f"Session {session_id} not found, cannot update title")
            return

        # Only update title if it's still the default
        if session.title and not session.title.startswith("Chat"):
            # Title already customized, don't override
            return

        # Generate title from user message
        title = "New Chat"
        if isinstance(user_input, list) and user_input:
            # For multimodal content, look for text content
            for item in user_input:
                if hasattr(item, "text") and item.text:
                    txt = item.text
                    title = txt[:50] + "..." if len(txt) > 50 else txt[:50]
                    break
        elif hasattr(user_input, "text"):
            txt = user_input.text
            title = txt[:50] + "..." if len(txt) > 50 else txt[:50]

        session.title = title

        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            await self.db.rollback()

    async def stream(
        self,
        agent,  # VirtualAgent object (already fetched with template)
        session_id: str,
        prompt,  # Can be str or InterleavedContent
    ):
        """
        Stream a response using the Responses API with Conversations.

        This method streams responses from LlamaStack using the Conversations API,
        which manages message history automatically.

        Args:
            agent: Virtual agent object (already fetched with template)
            session_id: Session ID
            prompt: User's message/input

        Yields:
            SSE-formatted JSON strings containing response chunks
        """
        try:
            # Build tools in Responses API format
            tools = await build_responses_tools(
                agent.tools, agent.vector_store_ids, self.request
            )

            # Prepare input with just the current message
            openai_input = await self._prepare_conversation_input(prompt)

            # Prepare streaming request parameters
            response_params = {
                "model": agent.model_name,
                "input": openai_input,
                "stream": True,  # Enable streaming!
            }

            # Add optional parameters
            if agent.temperature is not None:
                response_params["temperature"] = agent.temperature
            if agent.max_infer_iters is not None:
                response_params["max_infer_iters"] = agent.max_infer_iters
            if agent.prompt:
                response_params["instructions"] = agent.prompt
            if tools:
                response_params["tools"] = tools

            # Stream from LlamaStack - just forward everything to frontend
            async with get_client_from_request(self.request) as client:
                # Get or create conversation for this session
                conversation_id = await self._get_or_create_conversation(
                    session_id, client
                )
                response_params["conversation"] = conversation_id

                async for chunk in await client.responses.create(**response_params):
                    # Forward the chunk directly to frontend with session_id
                    chunk_dict = jsonable_encoder(chunk)
                    chunk_dict["session_id"] = str(session_id)
                    logger.info(f"Streaming chunk: {chunk_dict}")
                    yield f"data: {json.dumps(chunk_dict)}\n\n"

            logger.info(f"Stream loop completed for session {session_id}")

            # Send [DONE] to signal stream completion
            yield "data: [DONE]\n\n"

            # Update session title based on first message
            await self._update_session_title(agent.id, session_id, prompt)

        except Exception as e:
            logger.exception(f"Error in stream for agent {agent.id}: {e}")
            error_data = {
                "type": "error",
                "content": f"Error: {str(e)}",
                "session_id": str(session_id),
            }
            yield f"data: {json.dumps(jsonable_encoder(error_data))}\n\n"
