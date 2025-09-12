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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..api.llamastack import get_client_from_request
from .virtual_agents import get_virtual_agent_config

logger = logging.getLogger(__name__)


def build_responses_tools(
    tools: Optional[List[Any]], knowledge_base_ids: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """
    Convert virtual agent tools to OpenAI Responses API compatible format.

    The Responses API uses OpenAI-compatible tool patterns:
    - file_search for RAG/knowledge base queries
    - web_search for web searches
    - code_interpreter for code execution

    Args:
        tools: List of virtual agent tools to convert
        knowledge_base_ids: List of knowledge base IDs for file_search tools

    Returns:
        List of tools in OpenAI Responses API format
    """
    responses_tools = []

    if not tools:
        return responses_tools

    for tool_info in tools:
        if hasattr(tool_info, "toolgroup_id"):
            tool_id = tool_info.toolgroup_id
        elif isinstance(tool_info, dict):
            tool_id = tool_info.get("toolgroup_id")
        else:
            tool_id = str(tool_info)

        # Convert to OpenAI Responses API tool format
        if tool_id == "builtin::rag":
            if knowledge_base_ids:
                responses_tools.append(
                    {"type": "file_search", "vector_store_ids": knowledge_base_ids}
                )
        elif "web_search" in tool_id or "search" in tool_id:
            responses_tools.append({"type": "web_search"})
        elif "code" in tool_id or "interpreter" in tool_id:
            responses_tools.append({"type": "code_interpreter"})
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
        logger.info("=== Chat class initialized ===")
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
        logger.info(f"Looking up agent config for ID: {agent_id}")
        config = await get_virtual_agent_config(self.db, agent_id)
        if config:
            logger.info(f"Found agent config: {config.name}")
        else:
            logger.warning(f"No agent config found for ID: {agent_id}")
        return config

    async def create_response(
        self, agent_id: str, user_input: str, previous_response_id: Optional[str] = None
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
        logger.info(f"Creating response for agent {agent_id}")
        logger.info(f"User input: {user_input}")

        # Get virtual agent configuration from database
        agent_config = await self._get_virtual_agent_config(agent_id)
        if not agent_config:
            raise Exception(f"Virtual agent {agent_id} not found")

        # Build tools in Responses API format using agent config
        tools = build_responses_tools(
            agent_config.tools, agent_config.knowledge_base_ids
        )

        # Prepare response creation parameters using agent config
        response_params = {
            "model": agent_config.model_name,  # Use model from agent config
            "input": user_input,
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
            # Use the instructions parameter for system prompt in LlamaStack Responses API
            response_params["instructions"] = agent_config.prompt
            logger.info(f"Instructions: {agent_config.prompt}")

        # Add tools from agent config if any
        if tools:
            response_params["tools"] = tools

        # Add previous response for conversation chaining
        if previous_response_id:
            response_params["previous_response_id"] = previous_response_id

        # Note: Input/output shields not yet supported in Responses API
        if agent_config.input_shields:
            logger.warning("Input shields not yet supported in Responses API")
        if agent_config.output_shields:
            logger.warning("Output shields not yet supported in Responses API")

        logger.info(
            f"Creating response for agent {agent_id} with model {agent_config.model_name}"
        )

        try:
            # Call LlamaStack Responses API
            client = get_client_from_request(self.request)
            response = await client.responses.create(**response_params)

            # Extract content from response.output array
            content = ""
            if hasattr(response, "output") and response.output:
                for output_item in response.output:
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "text"):
                                content += content_item.text

            logger.info(f"LlamaStack response content: {content}")

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
        session_id: str,  # Keep for compatibility, but not used in Responses API
        prompt,  # Can be str or InterleavedContent
        agent_type_str: str = None,  # Keep for compatibility, but not used
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
            agent_type_str: Legacy agent type (not used in Responses API)
            previous_response_id: ID of previous response for conversation chaining

        Yields:
            JSON strings containing response chunks
        """
        try:
            # Convert InterleavedContent to string if needed
            if isinstance(prompt, list):
                # Extract text from InterleavedContent
                text_content = ""
                for item in prompt:
                    if hasattr(item, "text"):
                        text_content += item.text
                    elif isinstance(item, dict) and "text" in item:
                        text_content += item["text"]
                prompt_str = text_content
            elif isinstance(prompt, str):
                prompt_str = prompt
            else:
                prompt_str = str(prompt)

            # Create response using the virtual agent config
            response_data = await self.create_response(
                agent_id, prompt_str, previous_response_id
            )

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
                    "content": f"Error occurred while processing your request: {str(e)}",
                }
            )
