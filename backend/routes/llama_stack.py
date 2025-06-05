from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Literal, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from backend.database import get_db
import logging
from pydantic import BaseModel
from .chat import Chat
from ..api.llamastack import client
from .. import models
from fastapi import BackgroundTasks
from .virtual_assistants import read_virtual_assistant

class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str

class VAChatMessage(BaseModel):
    id: Optional[str] = None
    role: Literal['user', 'assistant', 'system']
    content: str
    parts: List[str] = []  # Add parts field to match useChat format

log = logging.getLogger(__name__)

router = APIRouter(prefix="/llama_stack", tags=["llama_stack"])

# Initialize LlamaStack client
@router.get("/llms", response_model=List[Dict[str, Any]])
async def get_llms():
    """Get available LLMs from LlamaStack"""
    try:
        log.info(f"Attempting to fetch models from LlamaStack at {client.base_url}")
        try:
            models = client.models.list()
            log.info(f"Received response from LlamaStack: {models}")
        except Exception as client_error:
            log.error(f"Error calling LlamaStack API: {str(client_error)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to LlamaStack API: {str(client_error)}"
            )

        if not models:
            log.warning("No models returned from LlamaStack")
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
                log.error(f"Error processing model data: {str(ae)}. Model data: {model}")
                continue

        log.info(f"Successfully processed {len(llms)} LLM models")
        return llms

    except Exception as e:
        log.error(f"Unexpected error in get_llms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/knowledge_bases", response_model=List[Dict[str, Any]])
async def get_knowledge_bases():
    """Get available knowledge bases from LlamaStack"""
    try:
        kbs = client.vector_dbs.list()
        return [{
            "kb_name": str(kb.identifier),
            "provider_resource_id": kb.provider_resource_id,
            "provider_id": kb.provider_id,
            "type": kb.type,
            "embedding_model": kb.embedding_model,
        } for kb in kbs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp_servers", response_model=List[Dict[str, Any]])
async def get_mcp_servers():
    """Get available MCP servers from LlamaStack"""
    try:
        servers = client.toolgroups.list()
        return [{
            "id": str(server.identifier),
            "name": server.provider_resource_id,
            "title": server.provider_id,
        } for server in servers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/safety_models", response_model=List[Dict[str, Any]])
async def get_safety_models():
    """Get available safety models from LlamaStack"""
    try:
        models = client.models.list()
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
async def get_embedding_models():
    """Get available embedding models from LlamaStack"""
    try:
        models = client.models.list()
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
async def get_shields():
    """Get available shields from LlamaStack"""
    try:
        shields = client.shields.list()
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
async def get_providers():
    """Get available providers from LlamaStack"""
    try:
        providers = client.providers.list()
        return [{
            "provider_id": str(provider.provider_id),
            "provider_type": provider.provider_type,
            "config": provider.config if hasattr(provider, 'config') else {},
            "api": provider.api
        } for provider in providers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    virtualAssistantId: str
    messages: list[Message]
    stream: bool = False
    sessionId: Optional[str] = None

@router.post("/chat")
async def chat(request: ChatRequest, background_task: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Chat endpoint that streams responses from LlamaStack"""
    try:
        log.info(f"Received request: {request.model_dump()}")
        
        # Get the agent directly from LlamaStack
        try:
            agent = client.agents.retrieve(agent_id=request.virtualAssistantId)
            log.info(f"Found agent: {agent.agent_id}")
        except Exception as e:
            log.error(f"Agent {request.virtualAssistantId} not found in LlamaStack: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Virtual assistant {request.virtualAssistantId} not found"
            )

        # Use the agent_id directly from LlamaStack 
        agent_id = request.virtualAssistantId
        
        # Session ID is required - no session creation in chat endpoint
        session_id = request.sessionId
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required. Please select or create a session first."
            )
        
        log.info(f"Using agent: {agent_id} with session: {session_id}")

        # Create stateless Chat instance (no longer needs assistant or session_state)
        chat = Chat(log)
        
        def generate_response():
            try:
                # Get the last user message
                if len(request.messages) > 0:
                    last_message = request.messages[-1]  # Get last message instead of popping
                    # Stream response using new stateless interface
                    for chunk in chat.stream(agent_id, session_id, last_message.content):
                        # Send the chunk directly since it's already properly formatted JSON
                        yield f"data: {chunk}\n\n"

                # End of stream
                yield f"data: [DONE]\n\n"
                
                # Save session metadata to database
                background_task.add_task(save_session_metadata, db, session_id, agent_id, request.messages)

            except Exception as e:
                log.error(f"Error in stream: {str(e)}")
                yield f"data: {{\"type\":\"error\",\"content\":\"Error: {str(e)}\"}}\n\n"

        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )

    except Exception as e:
        log.error(f"Error in chat endpoint: {str(e)}")
        #log.error(e.with_traceback())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def save_session_metadata(db: AsyncSession, session_id: str, agent_id: str, messages: list):
    """Save session metadata to database for sidebar display"""
    try:
        # Generate title from first user message
        title = "New Chat"
        if messages:
            # Find first user message for title
            for msg in messages:
                if msg.role == "user":
                    content = msg.content
                    title = content[:50] + "..." if len(content) > 50 else content
                    break
        
        # Get agent name
        agent_name = "Unknown Agent"
        try:
            # Fetch agent details from LlamaStack
            agent_details = await read_virtual_assistant(agent_id)
            agent_name = agent_details.get("name", f"Agent {agent_id[:8]}...")
        except Exception as e:
            log.error(f"Error fetching agent details: {e}")
            agent_name = f"Agent {agent_id[:8]}..."
        
        
        # Insert or update session metadata
        stmt = insert(models.ChatSession).values(
            id=session_id,
            title=title,
            agent_name=agent_name,
            session_state=json.dumps({"agent_id": agent_id, "session_id": session_id})
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_=dict(
                title=stmt.excluded.title,
                agent_name=stmt.excluded.agent_name,
                updated_at=stmt.excluded.updated_at
            )
        )
        
        await db.execute(stmt)
        await db.commit()
        log.info(f"Saved session metadata for {session_id}")
        
    except Exception as e:
        log.error(f"Error saving session metadata: {e}")
        await db.rollback()
