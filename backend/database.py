from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from .models import Base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print("############################################################")
print(f"DATABASE.PY: DATABASE_URL BEING USED: '{DATABASE_URL}'")
print("############################################################")
engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
