"""
Responses-based Chat implementation using LlamaStack's Responses API.

This module provides chat functionality using LlamaStack's modern Responses API
instead of the deprecated Agents API. Key features:
- Uses virtual agent configs as templates for model/tools/prompt
- Dynamically passes model and tools from config to each Responses API call
- Response chaining for conversation continuity
- OpenAI-compatible tool patterns
- No need for persistent agent creation
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..api.llamastack import get_client_from_request
from .virtual_agents import get_virtual_agent_config

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


class Chat:
    """
    A chat class using LlamaStack's Responses API with virtual agent configurations.

    This approach:
    - Uses virtual agent configs as templates for model/tools/prompt
    - Dynamically passes model and tools from config to each Responses API call
    - Chains conversations using previous_response_id
    - No need to pre-create persistent agents

    Args:
        request: FastAPI request object for LlamaStack client access
        db: Database session for accessing virtual agent configurations
    """

    def __init__(self, request: Request, db: AsyncSession):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.request = request
        self.db = db

    async def _get_virtual_agent_config(
        self, agent_id: str
    ) -> Optional[models.VirtualAgentConfig]:
        """
        Retrieve virtual agent configuration from our database.

        Args:
            agent_id: The unique identifier of the virtual agent

        Returns:
            VirtualAgentConfig object or None if not found
        """
        config = await get_virtual_agent_config(self.db, agent_id)
        if not config:
            logger.warning(f"No agent config found for ID: {agent_id}")
        return config

    async def create_response(
        self, agent_id: str, user_input, previous_response_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new response using the Responses API with virtual agent config.

        Args:
            agent_id: Virtual agent configuration ID
            user_input: User's message/input
            previous_response_id: ID of previous response for conversation chaining

        Returns:
            Response data including response ID and content

        Raises:
            Exception: If virtual agent not found or response creation fails
        """
        # Get virtual agent configuration from database
        agent_config = await self._get_virtual_agent_config(agent_id)
        if not agent_config:
            raise Exception(f"Virtual agent {agent_id} not found")

        # Build tools in Responses API format using agent config
        tools = await build_responses_tools(
            agent_config.tools, agent_config.vector_store_ids, self.request
        )

        # Use OpenAI message format for LlamaStack Responses API
        if isinstance(user_input, list):
            # For multimodal content, serialize Pydantic objects to dicts and
            # expand image URLs for LlamaStack
            content_items_for_llamastack = []
            for item in user_input:
                content_item = item.model_dump()
                expand_image_url(
                    content_item
                )  # Expand relative URLs to full URLs for LlamaStack
                content_items_for_llamastack.append(content_item)

            openai_input = [{"role": "user", "content": content_items_for_llamastack}]
        else:
            # For text-only content
            openai_input = str(user_input)

        # Prepare response creation parameters using agent config
        response_params = {
            "model": agent_config.model_name,  # Use model from agent config
            "input": openai_input,
        }

        # Add optional parameters from agent config
        param_mapping = {
            "temperature": "temperature",
        }

        for agent_attr, api_param in param_mapping.items():
            if hasattr(agent_config, agent_attr):
                value = getattr(agent_config, agent_attr)
                if value is not None and (
                    not isinstance(value, list) or len(value) > 0
                ):
                    response_params[api_param] = value

        # Add system prompt if available
        if agent_config.prompt:
            # Use the instructions parameter for system prompt in LlamaStack
            # Responses API
            response_params["instructions"] = agent_config.prompt

        # Add tools from agent config if any
        if tools:
            response_params["tools"] = tools

        # Add previous response for conversation chaining
        if previous_response_id:
            response_params["previous_response_id"] = previous_response_id

        # Always store messages for conversation history
        response_params["store"] = True

        # Note: Input/output shields not yet supported in Responses API
        if agent_config.input_shields:
            logger.warning("Input shields not yet supported in Responses API")
        if agent_config.output_shields:
            logger.warning("Output shields not yet supported in Responses API")

        try:
            # Call LlamaStack Responses API
            client = get_client_from_request(self.request)

            # Log the exact call parameters and client info
            logger.info(f"LlamaStack send: {response_params}")
            response = await client.responses.create(**response_params)
            logger.info(f"LlamaStack recv: {response}")

            # Extract content from response.output array
            content = ""
            if hasattr(response, "output") and response.output:
                for output_item in response.output:
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "text"):
                                content += content_item.text

            return {
                "response_id": response.id,
                "model": response.model,
                "usage": getattr(response, "usage", None),
                "content": content,
                "previous_response_id": previous_response_id,
                "agent_id": agent_id,
            }

        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            raise

    async def stream(
        self,
        agent_id: str,
        session_id: str,  # Session ID for updating session state
        prompt,  # Can be str or InterleavedContent
        previous_response_id: Optional[str] = None,
    ):
        """
        Stream a response using the Responses API with virtual agent configuration.

        This method maintains compatibility with the old interface while using
        the new Responses API under the hood.

        Args:
            agent_id: Virtual agent configuration ID
            session_id: Legacy session ID (not used in Responses API)
            prompt: User's message/input
            previous_response_id: ID of previous response for conversation chaining

        Yields:
            JSON strings containing response chunks
        """
        try:
            # Pass InterleavedContent directly to create_response to preserve images
            response_data = await self.create_response(
                agent_id, prompt, previous_response_id
            )

            # Session state will be updated by the background task in llama_stack.py

            # Stream the response content
            # TODO: When LlamaStack Responses API supports streaming, update this
            yield json.dumps(
                {
                    "type": "content",
                    "content": response_data["content"],
                    "response_id": response_data["response_id"],
                    "model": response_data["model"],
                }
            )

            # End stream marker
            yield json.dumps(
                {
                    "type": "done",
                    "response_id": response_data["response_id"],
                    "session_id": session_id,  # Return for compatibility
                }
            )

        except Exception as e:
            logger.error(f"Error in stream for agent {agent_id}: {e}")
            yield json.dumps(
                {
                    "type": "error",
                    "content": f"Error occurred while processing your request: "
                    f"{str(e)}",
                }
            )
