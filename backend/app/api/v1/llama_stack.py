"""
LlamaStack Integration API endpoints for direct LlamaStack operations.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, status

from ...api.llamastack import get_client_from_request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/llms", response_model=List[Dict[str, Any]])
async def get_llms(request: Request):
    """
    Retrieve all available Large Language Models from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        logger.info(f"Attempting to fetch models from LlamaStack at {client.base_url}")
        try:
            models = await client.models.list()
            logger.info(f"Received response from LlamaStack: {models}")
        except Exception as client_error:
            logger.error(f"Error calling LlamaStack API: {str(client_error)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to LlamaStack API: {str(client_error)}",
            )

        if not models:
            logger.warning("No models returned from LlamaStack")
            return []

        llms = []
        for model in models:
            try:
                if model.api_model_type == "llm":
                    llm_config = {
                        "model_name": str(model.identifier),
                        "provider_resource_id": model.provider_resource_id,
                        "model_type": model.api_model_type,
                    }
                    llms.append(llm_config)
            except AttributeError as ae:
                logger.error(
                    f"Error processing model data: {str(ae)}. Model data: {model}"
                )
                continue

        logger.info(f"Successfully processed {len(llms)} LLM models")
        return llms

    except Exception as e:
        logger.error(f"Unexpected error in get_llms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/tools", response_model=List[Dict[str, Any]])
async def get_tools(request: Request):
    """
    Retrieve all available MCP (Model Context Protocol) servers from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        servers = await client.toolgroups.list()
        return [
            {
                "id": str(server.identifier),
                "name": server.provider_resource_id,
                "title": server.provider_id,
                "toolgroup_id": str(server.identifier),
            }
            for server in servers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety_models", response_model=List[Dict[str, Any]])
async def get_safety_models(request: Request):
    """
    Retrieve all available safety models from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        models = await client.models.list()
        safety_models = []
        for model in models:
            if model.model_type == "safety":
                safety_model = {
                    "id": str(model.identifier),
                    "name": model.provider_resource_id,
                    "model_type": model.type,
                }
                safety_models.append(safety_model)
        return safety_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embedding_models", response_model=List[Dict[str, Any]])
async def get_embedding_models(request: Request):
    """
    Retrieve all available embedding models from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        models = await client.models.list()
        embedding_models = []
        for model in models:
            if model.model_type == "embedding":
                embedding_model = {
                    "name": str(model.identifier),
                    "provider_resource_id": model.provider_resource_id,
                    "model_type": model.type,
                }
                embedding_models.append(embedding_model)
        return embedding_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shields", response_model=List[Dict[str, Any]])
async def get_shields(request: Request):
    """
    Retrieve all available safety shields from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        shields = await client.shields.list()
        shields_list = []
        for shield in shields:
            shield = {
                "id": str(shield.identifier),
                "name": shield.provider_resource_id,
                "model_type": shield.type,
            }
            shields_list.append(shield)
        return shields_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=List[Dict[str, Any]])
async def get_providers(request: Request):
    """
    Retrieve all available providers from LlamaStack.
    """
    client = get_client_from_request(request)
    try:
        providers = await client.providers.list()
        return [
            {
                "provider_id": str(provider.provider_id),
                "provider_type": provider.provider_type,
                "config": (provider.config if hasattr(provider, "config") else {}),
                "api": provider.api,
            }
            for provider in providers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
