import asyncio
from backend.llamastack import LLAMASTACK_URL
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from llama_stack_client import LlamaStackClient, Agent
from llama_stack_client.types import UserMessage, SystemMessage, CompletionMessage, Tool
from typing import List, Dict, Any, AsyncGenerator, Literal, Optional, AsyncIterable
import logging
from pydantic import BaseModel
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import VirtualAssistant, VirtualAssistantTool, VirtualAssistantKnowledgeBase, KnowledgeBase
from backend.database import get_db
from uuid import UUID
import time

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
client = LlamaStackClient(base_url=LLAMASTACK_URL)

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
                if model.model_type == "llm":
                    llm_config = {
                        "id": str(model.identifier),
                        "name": model.provider_resource_id,
                        "model_type": model.model_type,
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
            "id": str(kb.identifier),
            "name": kb.provider_resource_id,
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
                    "id": str(model.identifier),
                    "name": model.provider_resource_id,
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

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = False

class VAChatRequest(BaseModel):
    messages: List[VAChatMessage]
    virtualAssistantId: str
    sessionId: Optional[str] = None
    agentId: Optional[str] = None

@router.post("/chat")
def chat(request: ChatRequest):
    """Chat endpoint that streams responses from LlamaStack"""
    try:
        log.info(f"Received request: {request.dict()}")
        # Get the list of available LLM model
        models = client.models.list()
        llm_model = None
        
        # If the requested model is available, use it
        for model in models:
            if model.model_type == "llm":
                if model.identifier == request.model:
                    llm_model = model
                    break

        if not llm_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No LLM model available"
            )

        # Convert Message objects to appropriate LlamaStack message types
        log.info(f"Processing messages: {request.messages}")
        llama_messages = []
        for msg in request.messages:
            if msg.role == 'user':
                llama_messages.append(UserMessage(role=msg.role, content=msg.content))
            elif msg.role == 'assistant':
                llama_messages.append(CompletionMessage(role=msg.role, content=msg.content, stop_reason='end_of_turn'))
            elif msg.role == 'system':
                llama_messages.append(SystemMessage(role=msg.role, content=msg.content))
        
        log.info(f"Using model: {llm_model.identifier}")
        log.info(f"Sending messages: {llama_messages}")
        
        def generate_response() -> AsyncGenerator[str, None]:
            try:
                # Get the response stream from LlamaStack
                response = client.inference.chat_completion(
                    model_id=llm_model.identifier,
                    messages=llama_messages,
                    stream=True
                )
                # Stream each chunk as it arrives
                log.info("Starting to stream response")
                for chunk in response:
                    if chunk and chunk.event and chunk.event.delta and chunk.event.delta.text:
                        log.info(f"Sending chunk: {chunk.event.delta.text}")
                        yield f"data: {chunk.event.delta.text}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                log.error(f"Error in stream: {str(e)}")
                yield f"data: Error: {str(e)}\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )

    except Exception as e:
        log.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/vachat")
async def virtual_assistant_chat(request: VAChatRequest, db: AsyncSession = Depends(get_db)):
    """Virtual Assistant Chat endpoint that follows Vercel AI SDK's format"""
    try:
        log.info(f"Received request: {request.dict()}")
        
        # Fetch virtual assistant configuration
        if not request.virtualAssistantId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Virtual assistant ID is required"
            )
        
        # Log the virtual assistant ID for debugging
        log.info(f"Looking up virtual assistant with ID: {request.virtualAssistantId}")
            
        # Convert string ID to UUID if needed
        try:
            va_id = UUID(request.virtualAssistantId)
            log.info(f"Converted ID to UUID: {va_id}")
        except ValueError as e:
            log.error(f"Invalid virtual assistant ID format: {request.virtualAssistantId}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid virtual assistant ID format"
            )

        # Execute async database query directly
        result = await db.execute(
            select(VirtualAssistant).where(VirtualAssistant.id == va_id)
        )
        va = result.scalar_one_or_none()

        if not va:
            log.error(f"Virtual assistant not found with ID: {va_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Virtual assistant not found with ID: {va_id}"
            )
            
        log.info(f"Found virtual assistant: {va.name} (ID: {va.id})")
        log.info(f"Virtual assistant model: {va.model_name}")
        log.info(f"Virtual assistant prompt: {va.prompt}")
        
        # Get the list of available LLM models
        models = client.models.list()
        log.info(f"Available models: {[m.identifier for m in models]}")
        llm_model = None
        
        # Use the model specified in the virtual assistant configuration
        for model in models:
            if model.model_type == "llm" and model.identifier == va.model_name:
                llm_model = model
                log.info(f"Found matching model: {model.identifier}")
                break
        
        if not llm_model:
            log.error(f"Model {va.model_name} not found in available models")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {va.model_name} not available"
            )

        # Fetch associated tools and knowledge bases
        tools_result = await db.execute(
            select(VirtualAssistantTool).where(VirtualAssistantTool.virtual_assistant_id == va.id)
        )
        mcp_tools = tools_result.scalars().all()
        log.info(f"Found {len(mcp_tools)} MCP tools")
        
        kb_result = await db.execute(
            select(VirtualAssistantKnowledgeBase).where(VirtualAssistantKnowledgeBase.virtual_assistant_id == va.id)
        )
        kb_relations = kb_result.scalars().all()
        log.info(f"Found {len(kb_relations)} knowledge base relations")

        # Get knowledge base details
        knowledge_bases = []
        for kb_rel in kb_relations:
            kb_result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == kb_rel.knowledge_base_id)
            )
            kb = kb_result.scalar_one_or_none()
            if kb:
                knowledge_bases.append(kb)
                log.info(f"Found knowledge base: {kb.name}")

        # Prepare tools list
        tools = []

        # Add MCP server tools
        for tool in mcp_tools:
            # Verify the tool is registered with LlamaStack
            try:
                tool_info = client.toolgroups.get(tool.mcp_server_id)
                if tool_info:
                    tools.append(tool.mcp_server_id)
                    log.info(f"Added MCP tool: {tool.mcp_server_id}")
            except Exception as e:
                log.warning(f"Tool {tool.mcp_server_id} not found in LlamaStack: {str(e)}")

        # Add RAG tools for each knowledge base
        for kb in knowledge_bases:
            try:
                # Verify the vector DB is registered with LlamaStack
                vector_db = client.vector_dbs.get(kb.vector_db_name)
                if vector_db:
                    # Create RAG tool configuration
                    rag_tool = {
                        "type": "rag",
                        "vector_db": kb.vector_db_name,
                        "embedding_model": kb.embedding_model,
                        "name": f"rag_{kb.name}"
                    }
                    tools.append(rag_tool)
                    log.info(f"Added RAG tool for: {kb.name}")
            except Exception as e:
                log.warning(f"Vector DB {kb.vector_db_name} not found in LlamaStack: {str(e)}")

        # Handle agent creation/reuse
        agent = None
        if request.agentId:
            try:
                # Try to get existing agent
                agent = client.agents.get(request.agentId)
                log.info(f"Using existing agent with ID: {request.agentId}")
            except Exception as e:
                log.warning(f"Error getting existing agent: {str(e)}. Will create new agent.")
                
        if not agent:

            log.info("Creating agent with parameters:")
            log.info(f"- Model: {llm_model.identifier}")
            log.info(f"- Tools: {tools}")
            log.info(f"- Instructions: {va.prompt}")

            agent = Agent(
                client=client,
                model=llm_model.identifier,
                tools=tools,
                sampling_params={},
                instructions=va.prompt,
                input_shields=[],
                output_shields=[]
            )

            log.info(f"Created new agent with ID: {agent.agent_id}")
            # Store agent ID to send in first chunk
            new_agent_id = agent.agent_id

        # Handle session management
        session_id = request.sessionId or f"va_{va.id}"
        log.info(f"Attempting to use va id as session ID: {session_id}")

        # Comprehensive session handling
        session = None
        try:
            # Multiple approaches to session creation/retrieval
            try:
                # First, try to retrieve existing session
                session = client.agents.session.retrieve(
                    session_id=session_id,
                    agent_id=agent.agent_id
                )
                log.info(f"Retrieved existing session: {session.session_id}")
            except Exception as retrieve_error:
                log.warning(f"Could not retrieve session: {retrieve_error}")

                # If retrieval fails, attempt to create a new session
                try:
                    session = client.agents.session.create(
                        session_name=va.name,
                        agent_id=agent.agent_id,
                    )
                    log.info(f"Created new session: {session}")
                except Exception as create_error:
                    log.error(f"Comprehensive session creation error: {create_error}")
                    log.error(f"Detailed error: {traceback.format_exc()}")
                    raise

        except Exception as final_error:
            log.critical(f"Unrecoverable session error: {final_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not establish session: {final_error}"
            )

        # Convert Message objects to LlamaStack message types
        llama_messages = []
        for msg in request.messages:
            if msg.role == 'user':
                llama_messages.append(UserMessage(role=msg.role, content=msg.content))
            elif msg.role == 'assistant':
                llama_messages.append(CompletionMessage(role=msg.role, content=msg.content, stop_reason='end_of_turn'))
            elif msg.role == 'system':
                llama_messages.append(SystemMessage(role=msg.role, content=msg.content))

        log.info(f"Converted messages to LlamaStack format: {llama_messages}")

        async def generate_response():
            try:
                # If we created a new agent, send its ID first
                if 'new_agent_id' in locals():
                    yield f"data: {json.dumps({'agent_id': new_agent_id})}\n\n"
                
                # Create a turn using the agent
                log.info(f"Creating turn with agent. Session ID: {session}")
                log.info(f"Messages: {[msg.content for msg in llama_messages]}")
                
                response = agent.create_turn(
                    session_id=session.session_id,  # Use the session ID we created/verified
                    messages=llama_messages,
                    stream=True
                )
                
                # Log response type and initial information
                log.info(f"Response type: {type(response)}")
                
                # Stream each chunk following Vercel AI SDK format
                for chunk in response:
                    if not chunk or not hasattr(chunk, 'event'):
                        log.warning(f"Skipping invalid chunk: {chunk}")
                        continue
                    
                    # Log detailed chunk information for debugging
                    log.info(f"Chunk event type: {type(chunk.event)}")
                    log.info(f"Chunk event attributes: {chunk.event}")

                    # Handle different turn response event types
                    try:
                        # Process step_progress events
                        if hasattr(chunk.event, 'step_progress'):
                            # Extract delta text from step_progress
                            text_delta = getattr(getattr(chunk.event.step_progress, 'delta', None), 'text', None)
                            
                            # Prepare step progress data
                            step_progress_data = {
                                "id": "turn-progress-" + str(chunk.event.id) if hasattr(chunk.event, 'id') else "turn-progress-default",
                                "object": "turn.progress",
                                "created": chunk.event.created if hasattr(chunk.event, 'created') else None,
                                "model": getattr(agent, 'model', 'unknown'),
                                "step_details": {
                                    "step_type": "inference",  # Explicitly set to inference
                                    "delta": text_delta
                                }
                            }
                            
                            # Send delta text if available
                            if text_delta:
                                chunk_data = {
                                    "id": "turn-chunk-" + str(chunk.event.id) if hasattr(chunk.event, 'id') else "turn-chunk-default",
                                    "object": "turn.chunk",
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "content": text_delta
                                        }
                                    }]
                                }
                                log.info(f"Sending turn text delta: {text_delta}")
                                yield f"data: {json.dumps(chunk_data)}\n\n"
                            
                            # Always send step progress details
                            log.info(f"Sending step progress details: {step_progress_data}")
                            yield f"data: {json.dumps(step_progress_data)}\n\n"
                        
                        # Process step_complete events
                        elif hasattr(chunk.event, 'step_complete'):
                            # Extract content from step_complete
                            content = getattr(chunk.event.step_complete, 'content', None)
                            
                            # Prepare step complete data
                            step_complete_data = {
                                "id": "turn-complete-" + str(chunk.event.id) if hasattr(chunk.event, 'id') else "turn-complete-default",
                                "object": "turn.complete",
                                "step_details": {
                                    "step_type": "inference",  # Explicitly set to inference
                                    "content": content
                                }
                            }
                            
                            # Send content if available
                            if content:
                                chunk_data = {
                                    "id": "turn-chunk-" + str(chunk.event.id) if hasattr(chunk.event, 'id') else "turn-chunk-default",
                                    "object": "turn.chunk",
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "content": content
                                        }
                                    }]
                                }
                                log.info(f"Sending turn content: {content}")
                                yield f"data: {json.dumps(chunk_data)}\n\n"
                            
                            # Always send step complete details
                            log.info(f"Sending step complete details: {step_complete_data}")
                            yield f"data: {json.dumps(step_complete_data)}\n\n"

                    except Exception as chunk_error:
                        log.error(f"Error processing chunk: {chunk_error}")
                        error_data = {
                            "error": {
                                "message": str(chunk_error)
                            }
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"

                # Send [DONE] message
                yield "data: [DONE]\n\n"
                await asyncio.sleep(0.1)

            except Exception as final_error:
                log.critical(f"Unrecoverable session error: {final_error}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error generating streaming response: {final_error}"
                )

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )

    except Exception as final_error:
        log.critical(f"Unrecoverable error in vachat endpoint: {final_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unrecoverable error in vachat endpoint: {final_error}"
        )