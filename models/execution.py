from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class Execution(BaseModel):
    """Execution model for tracking agent runs"""
    
    __tablename__ = "executions"

    input_data: Mapped[dict] = mapped_column(JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"  # pending, running, completed, failed
    )
    error_message: Mapped[Optional[str]] = mapped_column(nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    toolhouse_execution_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="executions")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")

    def __repr__(self) -> str:
        return f"Execution(id={self.id}, agent_id={self.agent_id}, status={self.status})" 