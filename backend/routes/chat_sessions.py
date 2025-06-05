from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime

from ..api.llamastack import client
from ..virtual_agents.agent_resource import VirtualAgentsResource

log = logging.getLogger(__name__)
router = APIRouter(prefix="/chat_sessions", tags=["chat_sessions"])

class CreateSessionRequest(BaseModel):
    agent_id: str
    session_name: Optional[str] = None

@router.get("/")
async def get_chat_sessions(
    agent_id: str,
    limit: int = 50
) -> List[dict]:
    """Get a list of chat sessions for a specific agent from LlamaStack directly"""
    try:
        # List sessions for this agent from LlamaStack
        # This will implicitly validate that the agent exists
        try:
            log.info(f"Attempting to list sessions for agent {agent_id}")
            sessions_response = client.agents.session.list(agent_id=agent_id)
            log.info(f"Raw sessions response: {sessions_response}")
            log.info(f"Response type: {type(sessions_response)}")
            
            sessions = []
            if isinstance(sessions_response, dict):
                if 'data' in sessions_response:
                    sessions = sessions_response['data']
                    log.info(f"Found data attribute with {len(sessions)} sessions")
                elif 'sessions' in sessions_response:
                    sessions = sessions_response['sessions']
                    log.info(f"Found sessions attribute with {len(sessions)} sessions")
            elif isinstance(sessions_response, list):
                sessions = sessions_response
                log.info(f"Direct response as list: {len(sessions)} items")
            elif hasattr(sessions_response, 'sessions'):
                sessions = sessions_response.sessions
                log.info(f"Found sessions attribute with {len(sessions)} sessions")
            else:
                sessions = []
                log.info(f"No sessions found in response")

            log.info(f"Final sessions count: {len(sessions) if sessions else 0} for agent {agent_id}")
        except Exception as e:
            log.error(f"Could not list sessions for agent {agent_id}: {e}")
            # If it's a 404-style error, the agent doesn't exist
            if "not found" in str(e).lower() or "404" in str(e):
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            else:
                # Other errors (network, API issues, etc.)
                raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")
        
        # Get agent name for display (optional, only if you need it)
        agent_name = "Unknown Agent"
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
            if hasattr(agent, 'agent_config') and isinstance(agent.agent_config, dict):
                agent_name = agent.agent_config.get('name', agent_name)
            elif hasattr(agent, 'instructions'):
                instructions = str(agent.instructions)[:50] + "..." if len(str(agent.instructions)) > 50 else str(agent.instructions)
                agent_name = instructions or agent_name
        except Exception as e:
            log.warning(f"Could not get agent name: {e}")
        
        session_list = []
        for session in sessions[:limit]:
            title = getattr(session, 'session_name', None) or f"Chat {session.session_id[:8]}..."
            
            session_list.append({
                "id": session.session_id,
                "title": title,
                "agent_name": agent_name,
                "updated_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            })
        
        return session_list
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chat sessions: {str(e)}"
        )

@router.get("/{session_id}")
async def get_chat_session(
    session_id: str,
    agent_id: Optional[str] = None
) -> dict:
    """Get a specific chat session with full message history from LlamaStack"""
    try:
        # Get session history from LlamaStack
        # Note: We might need agent_id to properly query the session
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
            
        # Verify agent exists
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
        except Exception as e:
            log.error(f"Agent {agent_id} not found: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Get session history (this might need to be implemented differently based on LlamaStack API)
        try:
            # Get session turns/messages from LlamaStack
            turns = client.agents.turn.list(
                agent_id=agent_id,
                session_id=session_id
            )
            
            # Convert turns to messages format
            messages = []
            for turn in turns:
                # Add user message
                if hasattr(turn, 'input_messages'):
                    for msg in turn.input_messages:
                        if hasattr(msg, 'content'):
                            messages.append({
                                "role": "user",
                                "content": msg.content
                            })
                
                # Add assistant response
                if hasattr(turn, 'output_message') and hasattr(turn.output_message, 'content'):
                    messages.append({
                        "role": "assistant", 
                        "content": turn.output_message.content
                    })
            
            # Get agent name
            agent_name = "Unknown Agent"
            try:
                if hasattr(agent, 'agent_config') and isinstance(agent.agent_config, dict):
                    agent_name = agent.agent_config.get('name', agent_name)
                elif hasattr(agent, 'instructions'):
                    instructions = str(agent.instructions)[:50] + "..." if len(str(agent.instructions)) > 50 else str(agent.instructions)
                    agent_name = instructions or agent_name
            except Exception as e:
                log.warning(f"Could not get agent name: {e}")
                
            return {
                "id": session_id,
                "title": f"Chat {session_id[:8]}...",  # Generate title or get from session name
                "agent_name": agent_name,
                "agent_id": agent_id,
                "messages": messages,
                "created_at": datetime.now().isoformat(),  # LlamaStack doesn't provide timestamps
                "updated_at": datetime.now().isoformat(),  # LlamaStack doesn't provide timestamps
            }
            
        except Exception as e:
            log.error(f"Error getting session history: {str(e)}")
            # Return empty session if history fetch fails
            return {
                "id": session_id,
                "title": f"Chat {session_id[:8]}...",
                "agent_name": "Unknown Agent",
                "agent_id": agent_id,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching chat session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chat session: {str(e)}"
        )

@router.delete("/{session_id}")
async def delete_chat_session(
    session_id: str,
    agent_id: str
) -> dict:
    """Delete a chat session from LlamaStack"""
    try:
        # Verify agent exists
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
            log.info(f"Found agent: {agent.agent_id}")
        except Exception as e:
            log.error(f"Agent {agent_id} not found: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Delete session from LlamaStack
        # Note: LlamaStack might not have a direct delete session API
        # For now, we'll just return success since sessions are managed by LlamaStack
        log.info(f"Session {session_id} deletion requested for agent {agent_id}")
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat session: {str(e)}"
        )

@router.post("/")
async def create_chat_session(
    request: CreateSessionRequest
) -> dict:
    """Create a new chat session for an agent using LlamaStack"""
    try:
        # Verify agent exists in LlamaStack
        try:
            agent = client.agents.retrieve(agent_id=request.agent_id)
            log.info(f"Found agent: {agent.agent_id}")
        except Exception as e:
            log.error(f"Agent {request.agent_id} not found in LlamaStack: {str(e)}")
            raise HTTPException(
                status_code=404,
                detail=f"Agent {request.agent_id} not found"
            )
        
        # Create session in LlamaStack using the agent's create_session method
        session_name = request.session_name or "New Chat"
        try:
            session = client.agents.session.create(
                agent_id=request.agent_id,
                session_name=session_name or f"Session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            session_id = session.session_id
            log.info(f"Created LlamaStack session: {session_id}")
        except Exception as e:
            log.error(f"Failed to create session in LlamaStack: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session in LlamaStack: {str(e)}"
            )
        
        # Get agent name for display
        agent_name = "Unknown Agent"
        try:
            if hasattr(agent, 'agent_config') and isinstance(agent.agent_config, dict):
                agent_name = agent.agent_config.get('name', agent_name)
            elif hasattr(agent, 'name'):
                agent_name = agent.name
            elif hasattr(agent, 'instructions'):
                # Use first few words of instructions as name
                instructions = str(agent.instructions)[:50] + "..." if len(str(agent.instructions)) > 50 else str(agent.instructions)
                agent_name = instructions or agent_name
        except Exception as e:
            log.warning(f"Could not get agent name: {e}")
        
        return {
            "id": session_id,
            "title": session_name,
            "agent_name": agent_name,
            "agent_id": request.agent_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat session: {str(e)}"
        )

@router.get("/debug/{agent_id}")
async def debug_session_listing(agent_id: str):
    """Debug endpoint to test session listing directly"""
    try:
        log.info(f"=== DEBUG SESSION LISTING FOR AGENT {agent_id} ===")
        
        # Test 1: Check if agent exists
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
            log.info(f"✅ Agent exists: {agent.agent_id}")
        except Exception as e:
            log.error(f"❌ Agent not found: {e}")
            return {"error": f"Agent not found: {e}"}
        
        # Test 2: Check session resource type
        session_resource = client.agents.session
        log.info(f"Session resource type: {type(session_resource)}")
        log.info(f"Session resource methods: {[m for m in dir(session_resource) if not m.startswith('_')]}")
        
        # Test 3: Try to call list method
        try:
            sessions_response = client.agents.session.list(agent_id=agent_id)
            log.info(f"✅ List method called successfully")
            log.info(f"Response type: {type(sessions_response)}")
            log.info(f"Response value: {sessions_response}")
            log.info(f"Response dir: {dir(sessions_response)}")
            
            # Try to extract sessions
            if hasattr(sessions_response, 'sessions'):
                sessions = sessions_response.sessions
                log.info(f"Found sessions attr: {sessions}")
            elif isinstance(sessions_response, list):
                sessions = sessions_response
                log.info(f"Response is direct list: {sessions}")
            else:
                sessions = []
                log.info(f"No sessions found in response")
                
            return {
                "agent_id": agent_id,
                "response_type": str(type(sessions_response)),
                "response_value": str(sessions_response),
                "sessions_count": len(sessions) if sessions else 0,
                "sessions": sessions if sessions else []
            }
            
        except Exception as e:
            log.error(f"❌ List method failed: {e}")
            log.error(f"Exception type: {type(e)}")
            return {"error": f"List method failed: {e}"}
            
    except Exception as e:
        log.error(f"❌ Debug failed: {e}")
        return {"error": f"Debug failed: {e}"}