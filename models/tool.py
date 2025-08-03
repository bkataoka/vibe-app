from typing import Optional, List
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class Tool(BaseModel):
    """Tool model for managing available tools"""
    
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(255), index=True)
    schema: Mapped[dict] = mapped_column(JSON)  # Input/output schema
    configuration: Mapped[dict] = mapped_column(JSON, default={})
    toolhouse_tool_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tools")
    agent_tools: Mapped[List["AgentTool"]] = relationship("AgentTool", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Tool(id={self.id}, name={self.name}, version={self.version})"


class AgentTool(BaseModel):
    """Association model between Agents and Tools"""
    
    __tablename__ = "agent_tools"

    # Foreign Keys
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"))
    
    # Additional fields
    configuration: Mapped[dict] = mapped_column(JSON, default={})  # Tool-specific config for this agent
    is_enabled: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="agent_tools")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="agent_tools")

    def __repr__(self) -> str:
        return f"AgentTool(agent_id={self.agent_id}, tool_id={self.tool_id}, enabled={self.is_enabled})" 