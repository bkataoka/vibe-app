from typing import Optional, List
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class Agent(BaseModel):
    """Agent model for managing AI agents"""
    
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), index=True)
    configuration: Mapped[dict] = mapped_column(JSON, default={})
    toolhouse_agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="inactive",  # inactive, active, error
    )
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agents")
    executions: Mapped[List["Execution"]] = relationship("Execution", back_populates="agent", cascade="all, delete-orphan")
    agent_tools: Mapped[List["AgentTool"]] = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Agent(id={self.id}, name={self.name}, status={self.status})" 