from fastapi import FastAPI
from .database import engine, Base

from .routes import users, mcp_servers, knowledge_bases, virtual_assistants, chat_history, guardrails

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(users.router)
app.include_router(mcp_servers.router)
app.include_router(knowledge_bases.router)
app.include_router(virtual_assistants.router)
app.include_router(chat_history.router)
app.include_router(guardrails.router)