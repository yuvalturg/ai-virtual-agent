from fastapi import FastAPI
from .database import engine, Base, AsyncSessionLocal
from .routes import users, mcp_servers, knowledge_bases, virtual_assistants, chat_history, guardrails, model_servers
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

load_dotenv()


app = FastAPI()

origins = ["*"]  # Update this with the frontend domain in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        async with AsyncSessionLocal() as session:
            await mcp_servers.sync_mcp_servers(session)
    except Exception as e:
        print(f"Failed to sync MCP servers on startup: {str(e)}")
    
    async with AsyncSessionLocal() as session:
        try:
            await model_servers.sync_model_servers(session)
        except Exception as e:
            print(f"Failed to sync model servers on startup: {str(e)}")
    
    async with AsyncSessionLocal() as session:
        try:
            await knowledge_bases.sync_knowledge_bases(session)
        except Exception as e:
            print(f"Failed to sync knowledge bases on startup: {str(e)}")

app.include_router(users.router)
app.include_router(mcp_servers.router)
app.include_router(knowledge_bases.router)
app.include_router(virtual_assistants.router)
app.include_router(chat_history.router)
app.include_router(guardrails.router)
app.include_router(model_servers.router)



