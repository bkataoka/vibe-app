from typing import Optional, Dict, List, ForwardRef
from pydantic import BaseModel, ConfigDict

from schemas.base import BaseSchema, BaseCreateSchema, BaseUpdateSchema

# Forward references for circular imports
AgentBase = ForwardRef("AgentBase")


class ToolBase(BaseModel):
    """Base schema for Tool"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Sample Tool",
                "schema": {"type": "object"},
                "configuration": {"key": "value"},
                "version": "1.0.0"
            }
        }
    )
    
    name: str
    schema: Dict
    configuration: Dict = {}
    version: str = "1.0.0"


class ToolCreate(BaseCreateSchema, ToolBase):
    """Schema for creating a new tool"""
    pass


class ToolUpdate(BaseUpdateSchema):
    """Schema for updating a tool"""
    name: Optional[str] = None
    schema: Optional[Dict] = None
    configuration: Optional[Dict] = None
    version: Optional[str] = None
    toolhouse_tool_id: Optional[str] = None


class ToolInDBBase(BaseSchema, ToolBase):
    """Base schema for Tool in DB"""
    user_id: int
    toolhouse_tool_id: Optional[str] = None


class Tool(ToolInDBBase):
    """Schema for Tool with relationships"""
    pass


class AgentToolBase(BaseModel):
    """Base schema for AgentTool association"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "configuration": {"key": "value"},
                "is_enabled": True
            }
        }
    )
    
    configuration: Dict = {}
    is_enabled: bool = True


class AgentToolCreate(BaseCreateSchema, AgentToolBase):
    """Schema for creating a new agent-tool association"""
    agent_id: int
    tool_id: int


class AgentToolUpdate(BaseUpdateSchema):
    """Schema for updating an agent-tool association"""
    configuration: Optional[Dict] = None
    is_enabled: Optional[bool] = None


class AgentToolInDBBase(BaseSchema, AgentToolBase):
    """Base schema for AgentTool in DB"""
    agent_id: int
    tool_id: int


class AgentTool(AgentToolInDBBase):
    """Schema for AgentTool with relationships"""
    tool: Tool


class ToolWithAgents(Tool):
    """Schema for Tool with associated agents"""
    agents: List[AgentBase] = []


# Update forward references after all classes are defined
from schemas.agent import AgentBase  # noqa: E402

ToolWithAgents.model_rebuild() 