"""
Profile API endpoint to fetch an authorized user's details.

This module provides a read operation that returns an authorized user's information.

Key Features:
- Simple authorization check
- User lookup
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=schemas.UserRead)
@router.get("/", response_model=schemas.UserRead)
async def read_profile(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Retrieve an authorized user's profile.

    This endpoint fetches an authorized user's profile information.

    Args:
        request: HTTP request details
        db: Database session dependency

    Returns:
        schemas.UserRead: The authorized user's profile

    Raises:
        HTTPException: 401 if the user is not authorized
        HTTPException: 403 if the user is not found
    """
    username = request.headers.get("X-Forwarded-User")
    email = request.headers.get("X-Forwarded-Email")
    if not username and not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    result = await db.execute(
        select(models.User).where(
            (models.User.username == username) | (models.User.email == email)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not found"
        )
    return user
