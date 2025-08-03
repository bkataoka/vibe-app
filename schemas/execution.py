from datetime import datetime
from typing import Optional, Dict, ForwardRef
from pydantic import BaseModel, ConfigDict

from schemas.base import BaseSchema, BaseCreateSchema, BaseUpdateSchema

# Forward references for circular imports
Agent = ForwardRef("Agent")


class ExecutionBase(BaseModel):
    """Base schema for Execution"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "input_data": {"key": "value"},
                "status": "pending"
            }
        }
    )
    
    input_data: Dict
    status: str = "pending"


class ExecutionCreate(BaseCreateSchema, ExecutionBase):
    """Schema for creating a new execution"""
    agent_id: int


class ExecutionUpdate(BaseUpdateSchema):
    """Schema for updating an execution"""
    output_data: Optional[Dict] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    toolhouse_execution_id: Optional[str] = None


class ExecutionInDBBase(BaseSchema, ExecutionBase):
    """Base schema for Execution in DB"""
    user_id: int
    agent_id: int
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    toolhouse_execution_id: Optional[str] = None


class Execution(ExecutionInDBBase):
    """Schema for Execution with relationships"""
    agent: Optional[Agent] = None


class ExecutionResult(BaseModel):
    """Schema for execution results"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "execution_id": 1,
                "status": "completed",
                "output_data": {"result": "success"},
                "error_message": None,
                "completed_at": "2024-01-20T12:00:00Z"
            }
        }
    )
    
    execution_id: int
    status: str
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


# Update forward references after all classes are defined
from schemas.agent import Agent  # noqa: E402

Execution.model_rebuild() 