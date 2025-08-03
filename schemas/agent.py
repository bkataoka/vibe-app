from typing import Optional, Dict, List, ForwardRef
from pydantic import BaseModel, ConfigDict

from schemas.base import BaseSchema, BaseCreateSchema, BaseUpdateSchema

# Forward references for circular imports
ToolBase = ForwardRef("ToolBase")
ExecutionBase = ForwardRef("ExecutionBase")


class AgentBase(BaseModel):
    """Base schema for Agent"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Sample Agent",
                "configuration": {"key": "value"},
                "status": "inactive"
            }
        }
    )
    
    name: str
    configuration: Dict = {}
    status: str = "inactive"


class AgentCreate(BaseCreateSchema, AgentBase):
    """Schema for creating a new agent"""
    pass


class AgentUpdate(BaseUpdateSchema):
    """Schema for updating an agent"""
    name: Optional[str] = None
    configuration: Optional[Dict] = None
    status: Optional[str] = None
    toolhouse_agent_id: Optional[str] = None


class AgentInDBBase(BaseSchema, AgentBase):
    """Base schema for Agent in DB"""
    user_id: int
    toolhouse_agent_id: Optional[str] = None


class Agent(AgentInDBBase):
    """Schema for Agent with relationships"""
    pass


class AgentWithTools(Agent):
    """Schema for Agent with associated tools"""
    tools: List[ToolBase] = []


class AgentWithExecutions(Agent):
    """Schema for Agent with execution history"""
    executions: List[ExecutionBase] = []


class AgentComplete(Agent):
    """Complete Agent schema with all relationships"""
    tools: List[ToolBase] = []
    executions: List[ExecutionBase] = []


# Update forward references after all classes are defined
from schemas.tool import ToolBase  # noqa: E402
from schemas.execution import ExecutionBase  # noqa: E402

AgentComplete.model_rebuild()
AgentWithTools.model_rebuild()
AgentWithExecutions.model_rebuild() 