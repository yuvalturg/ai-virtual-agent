#!/usr/bin/env python3
"""Test script to debug session listing issue"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.llamastack import client

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_session_operations():
    """Test session creation and listing"""
    
    print("=== LlamaStack Session Testing ===")
    
    # Step 1: List available agents
    try:
        agents = client.agents.list()
        print(f"✅ Found {len(agents)} agents")
        if not agents:
            print("❌ No agents found - cannot test sessions")
            return
        
        # Use the first agent for testing
        test_agent = agents[0]
        agent_id = test_agent.agent_id
        print(f"🔍 Testing with agent: {agent_id}")
        
    except Exception as e:
        print(f"❌ Failed to list agents: {e}")
        return
    
    # Step 2: Check session resource type
    session_resource = client.agents.session
    print(f"📦 Session resource type: {type(session_resource)}")
    print(f"📋 Available methods: {[m for m in dir(session_resource) if not m.startswith('_')]}")
    
    # Step 3: Try to list existing sessions
    try:
        print(f"🔍 Attempting to list sessions for agent {agent_id}")
        sessions = client.agents.session.list(agent_id=agent_id)
        print(f"✅ Sessions list successful!")
        print(f"📊 Response type: {type(sessions)}")
        print(f"📄 Response value: {sessions}")
        
        # Try to parse sessions
        if hasattr(sessions, 'sessions'):
            actual_sessions = sessions.sessions
            print(f"📝 Found sessions attribute with {len(actual_sessions)} sessions")
        elif isinstance(sessions, list):
            actual_sessions = sessions
            print(f"📝 Direct list with {len(actual_sessions)} sessions")
        else:
            actual_sessions = []
            print(f"📝 No sessions found")
            
        print(f"🎯 Final session count: {len(actual_sessions)}")
        
    except Exception as e:
        print(f"❌ Failed to list sessions: {e}")
        print(f"🔧 Exception type: {type(e)}")
        if hasattr(e, 'status_code'):
            print(f"🌐 HTTP status: {e.status_code}")
            
    # Step 4: Try to create a test session
    try:
        print(f"🔨 Attempting to create a test session")
        session_name = "Test Session"
        new_session = client.agents.session.create(
            agent_id=agent_id,
            session_name=session_name
        )
        print(f"✅ Session creation successful!")
        print(f"🆔 New session ID: {new_session.session_id}")
        
        # Now try listing again
        print(f"🔍 Re-attempting to list sessions after creation")
        sessions = client.agents.session.list(agent_id=agent_id)
        
        if hasattr(sessions, 'sessions'):
            actual_sessions = sessions.sessions
        elif isinstance(sessions, list):
            actual_sessions = sessions
        else:
            actual_sessions = []
            
        print(f"🎯 Session count after creation: {len(actual_sessions)}")
        
        # Clean up - delete the test session
        try:
            client.agents.session.delete(
                session_id=new_session.session_id,
                agent_id=agent_id
            )
            print(f"🗑️ Test session deleted")
        except Exception as e:
            print(f"⚠️ Failed to delete test session: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        print(f"🔧 Exception type: {type(e)}")
        if hasattr(e, 'status_code'):
            print(f"🌐 HTTP status: {e.status_code}")

if __name__ == "__main__":
    test_session_operations()
