"""
Dependency functions for FastAPI endpoints.
"""

from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal


async def get_db() -> Generator[AsyncSession, None, None]:
    """
    Dependency function that provides database sessions for FastAPI endpoints.

    Yields:
        AsyncSession: Database session that automatically handles cleanup
    """
    async with AsyncSessionLocal() as session:
        yield session
