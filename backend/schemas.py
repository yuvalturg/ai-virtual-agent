from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional, List, Any
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    devops = "devops"
    user = "user"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: RoleEnum

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: UUID4
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True

class MCPServerBase(BaseModel):
    name: str
    title: str
    description: Optional[str]
    endpoint_url: str
    configuration: Optional[dict]

class MCPServerCreate(MCPServerBase):
    pass

class MCPServerRead(MCPServerBase):
    id: UUID4
    created_by: Optional[UUID4]
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True

class KnowledgeBaseBase(BaseModel):
    name: str
    version: str
    embedding_model: str
    provider_id: Optional[str]
    vector_db_name: str
    is_external: bool = False
    source: Optional[str]
    source_configuration: Optional[dict]

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseRead(KnowledgeBaseBase):
    id: UUID4
    created_by: Optional[UUID4]
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True

class VirtualAssistantBase(BaseModel):
    name: str
    prompt: str
    model_name: str
    knowledge_base_ids: List[str]
    tool_ids: List[str]

class VirtualAssistantCreate(VirtualAssistantBase):
    pass

class VirtualAssistantUpdate(VirtualAssistantBase):
    pass

class VirtualAssistantRead(VirtualAssistantBase):
    id: UUID4
    created_by: Optional[UUID4]
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True

class ChatHistoryBase(BaseModel):
    virtual_assistant_id: UUID4
    user_id: UUID4
    message: str
    response: str

class ChatHistoryCreate(ChatHistoryBase):
    pass

class ChatHistoryRead(ChatHistoryBase):
    id: UUID4
    created_at: Any

    class Config:
        orm_mode = True

class GuardrailBase(BaseModel):
    name: str
    rules: dict

class GuardrailCreate(GuardrailBase):
    pass

class GuardrailRead(GuardrailBase):
    id: UUID4
    created_by: Optional[UUID4]
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True


class ModelServerBase(BaseModel):
    name: str
    provider_name: str
    model_name: str
    endpoint_url: str
    token: Optional[str] = None

class ModelServerCreate(ModelServerBase):
    pass

class ModelServerUpdate(ModelServerBase):
    pass

class ModelServerRead(ModelServerBase):
    id: UUID4

    class Config:
        orm_mode = True


