# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from llama_stack_client import BaseModel
from llama_stack_client.types.shared_params.agent_config import AgentConfig

__all__ = ["VirtualAgent","VirtualAgentListResponse"]


class VirtualAgent(BaseModel):
    agent_id: str
    agent_config: AgentConfig
    type: Literal["virtual_agent"]

VirtualAgentListResponse: TypeAlias = List[VirtualAgent]
