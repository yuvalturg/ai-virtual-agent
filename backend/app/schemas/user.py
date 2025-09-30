"""
User-related schemas.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from ..models.user import RoleEnum
from .base import BaseSchema, TimestampMixin


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str
    email: EmailStr
    role: RoleEnum
    agent_ids: List[str] = []


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    agent_ids: Optional[List[str]] = None


class UserInDB(UserBase, TimestampMixin, BaseSchema):
    """Schema for user as stored in database."""

    id: UUID


class UserResponse(UserInDB):
    """Schema for user in API responses."""

    pass


class UserAgentAssignment(BaseModel):
    """Schema for assigning/removing agents to/from a user."""

    agent_ids: List[str]
