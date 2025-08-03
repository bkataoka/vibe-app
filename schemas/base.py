from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common fields"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "created_at": "2024-01-20T12:00:00Z",
                "updated_at": "2024-01-20T12:00:00Z",
                "is_active": True,
                "description": "Sample description"
            }
        }
    )

    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    description: Optional[str] = None


class BaseCreateSchema(BaseModel):
    """Base schema for creation without auto-generated fields"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "description": "Sample description"
            }
        }
    )
    
    description: Optional[str] = None


class BaseUpdateSchema(BaseModel):
    """Base schema for updates"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "description": "Updated description",
                "is_active": True
            }
        }
    )
    
    description: Optional[str] = None
    is_active: Optional[bool] = None 