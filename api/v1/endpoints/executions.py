from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.v1.deps import AsyncSessionDep, CurrentUser
from core.toolhouse import toolhouse_client
from core.websockets import manager
from models.execution import Execution
from models.agent import Agent
from schemas.execution import (
    Execution as ExecutionSchema,
    ExecutionCreate,
    ExecutionUpdate,
    ExecutionResult,
)

router = APIRouter()


async def send_execution_update(
    execution: Execution,
    update_type: str,
    additional_data: dict = None,
) -> None:
    """Send execution update via WebSocket."""
    data = {
        "execution_id": execution.id,
        "status": execution.status,
        "output_data": execution.output_data,
        "error_message": execution.error_message,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }
    if additional_data:
        data.update(additional_data)
    
    # Send to execution-specific subscribers
    await manager.broadcast_to_execution(execution.id, update_type, data)
    # Send to user's general connection
    await manager.broadcast_to_user(execution.user_id, update_type, data)


async def process_execution(
    db: AsyncSessionDep,
    execution_id: int,
) -> None:
    """Process an execution in the background."""
    # Get execution
    execution = await db.get(Execution, execution_id)
    if not execution:
        return
    
    try:
        # Update status to running
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        await db.commit()
        await send_execution_update(execution, "execution_started")
        
        # Get agent
        agent = await db.get(Agent, execution.agent_id)
        if not agent or not agent.toolhouse_agent_id:
            raise ValueError("Agent not found or not registered with Toolhouse")
        
        # Start execution in Toolhouse
        toolhouse_execution_id = await toolhouse_client.start_execution(
            agent_id=agent.toolhouse_agent_id,
            input_data=execution.input_data,
        )
        
        # Update execution with Toolhouse ID
        execution.toolhouse_execution_id = toolhouse_execution_id
        await db.commit()
        
        # Poll for execution status
        last_status = execution.status
        while True:
            status_data = await toolhouse_client.get_execution_status(toolhouse_execution_id)
            current_status = status_data.get("status", "unknown")
            
            # Send update if status changed
            if current_status != last_status:
                execution.status = current_status
                execution.output_data = status_data.get("output_data")
                execution.error_message = status_data.get("error_message")
                await send_execution_update(
                    execution,
                    "execution_status_changed",
                    {"previous_status": last_status}
                )
                last_status = current_status
            
            if current_status in ["completed", "failed"]:
                execution.completed_at = datetime.utcnow()
                break
            
            # Add a small delay between polls
            import asyncio
            await asyncio.sleep(2)
        
        # Send final update
        await send_execution_update(
            execution,
            "execution_completed" if execution.status == "completed" else "execution_failed"
        )
        
    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()
        await send_execution_update(execution, "execution_failed")
    
    await db.commit()


@router.get("/", response_model=List[ExecutionSchema])
async def list_executions(
    db: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all executions."""
    query = select(Execution)
    if not current_user.is_superuser:
        query = query.where(Execution.user_id == current_user.id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ExecutionSchema)
async def create_execution(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    execution_in: ExecutionCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """Create a new execution."""
    # Check if agent exists and user has access
    agent = await db.get(Agent, execution_in.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    if not current_user.is_superuser and agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if agent is registered with Toolhouse
    if not agent.toolhouse_agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent not registered with Toolhouse",
        )
    
    execution = Execution(
        **execution_in.model_dump(),
        user_id=current_user.id,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # Send creation notification
    await send_execution_update(execution, "execution_created")
    
    # Start processing in background
    background_tasks.add_task(process_execution, db, execution.id)
    
    return execution


@router.get("/{execution_id}", response_model=ExecutionSchema)
async def get_execution(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    execution_id: int,
) -> Any:
    """Get execution by ID."""
    query = (
        select(Execution)
        .where(Execution.id == execution_id)
        .options(selectinload(Execution.agent))
    )
    if not current_user.is_superuser:
        query = query.where(Execution.user_id == current_user.id)
    
    result = await db.execute(query)
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    return execution


@router.get("/{execution_id}/result", response_model=ExecutionResult)
async def get_execution_result(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    execution_id: int,
) -> Any:
    """Get execution result."""
    execution = await get_execution(
        db=db,
        current_user=current_user,
        execution_id=execution_id,
    )
    
    # If execution has Toolhouse ID and is still running, get latest status
    if execution.toolhouse_execution_id and execution.status == "running":
        try:
            status_data = await toolhouse_client.get_execution_status(
                execution.toolhouse_execution_id
            )
            current_status = status_data.get("status", execution.status)
            
            if current_status != execution.status:
                execution.status = current_status
                execution.output_data = status_data.get("output_data")
                execution.error_message = status_data.get("error_message")
                if current_status in ["completed", "failed"]:
                    execution.completed_at = datetime.utcnow()
                await db.commit()
                
                # Send status update
                await send_execution_update(
                    execution,
                    "execution_status_changed",
                    {"previous_status": execution.status}
                )
        
        except Exception:
            # If we can't get the status, return the current execution data
            pass
    
    return ExecutionResult(
        execution_id=execution.id,
        status=execution.status,
        output_data=execution.output_data,
        error_message=execution.error_message,
        completed_at=execution.completed_at,
    )


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    execution_id: int,
) -> None:
    """Delete an execution."""
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    if not current_user.is_superuser and execution.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # If execution is running and has Toolhouse ID, try to stop it
    if execution.status == "running" and execution.toolhouse_execution_id:
        try:
            await toolhouse_client.stop_execution(execution.toolhouse_execution_id)
            # Send cancellation notification
            await send_execution_update(
                execution,
                "execution_cancelled",
                {"reason": "User requested cancellation"}
            )
        except Exception:
            # Continue with deletion even if we can't stop the execution
            pass
    
    await db.delete(execution)
    await db.commit() 