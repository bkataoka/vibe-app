from typing import Any, List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.v1.deps import AsyncSessionDep, CurrentUser
from core.toolhouse import toolhouse_client
from models.tool import Tool, AgentTool
from models.agent import Agent
from schemas.tool import (
    Tool as ToolSchema,
    ToolCreate,
    ToolUpdate,
    AgentTool as AgentToolSchema,
    AgentToolCreate,
    AgentToolUpdate,
    ToolWithAgents,
)

router = APIRouter()


@router.get("/", response_model=List[ToolSchema])
async def list_tools(
    db: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all tools."""
    query = select(Tool)
    if not current_user.is_superuser:
        query = query.where(Tool.user_id == current_user.id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ToolSchema)
async def create_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    tool_in: ToolCreate,
) -> Any:
    """Create a new tool."""
    try:
        # Register tool with Toolhouse
        toolhouse_tool_id = await toolhouse_client.register_tool(
            name=tool_in.name,
            schema=tool_in.schema,
            configuration=tool_in.configuration,
        )
        
        # Create tool in database
        tool = Tool(
            **tool_in.model_dump(),
            user_id=current_user.id,
            toolhouse_tool_id=toolhouse_tool_id,
        )
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        return tool
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tool: {str(e)}",
        )


@router.get("/{tool_id}", response_model=ToolWithAgents)
async def get_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    tool_id: int,
) -> Any:
    """Get tool by ID."""
    query = (
        select(Tool)
        .where(Tool.id == tool_id)
        .options(selectinload(Tool.agent_tools).selectinload(Tool.agent))
    )
    if not current_user.is_superuser:
        query = query.where(Tool.user_id == current_user.id)
    
    result = await db.execute(query)
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    return tool


@router.put("/{tool_id}", response_model=ToolSchema)
async def update_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    tool_id: int,
    tool_in: ToolUpdate,
) -> Any:
    """Update a tool."""
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    if not current_user.is_superuser and tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        # Update tool in Toolhouse if configuration changed
        if tool_in.configuration is not None and tool.toolhouse_tool_id:
            await toolhouse_client.update_tool(
                tool_id=tool.toolhouse_tool_id,
                configuration=tool_in.configuration,
            )
        
        # Update tool attributes
        for field, value in tool_in.model_dump(exclude_unset=True).items():
            setattr(tool, field, value)
        
        await db.commit()
        await db.refresh(tool)
        return tool
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update tool: {str(e)}",
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    tool_id: int,
) -> None:
    """Delete a tool."""
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    if not current_user.is_superuser and tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Note: We don't delete the tool from Toolhouse as it might be used by other systems
    # or needed for historical data
    
    await db.delete(tool)
    await db.commit()


# Agent-Tool Association Endpoints

@router.post("/agent-tools", response_model=AgentToolSchema)
async def create_agent_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_tool_in: AgentToolCreate,
) -> Any:
    """Associate a tool with an agent."""
    # Check if agent and tool exist and user has access
    agent = await db.get(Agent, agent_tool_in.agent_id)
    tool = await db.get(Tool, agent_tool_in.tool_id)
    
    if not agent or not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent or Tool not found",
        )
    
    if not current_user.is_superuser:
        if agent.user_id != current_user.id or tool.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    agent_tool = AgentTool(
        **agent_tool_in.model_dump(),
    )
    db.add(agent_tool)
    await db.commit()
    await db.refresh(agent_tool)
    return agent_tool


@router.put("/agent-tools/{agent_tool_id}", response_model=AgentToolSchema)
async def update_agent_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_tool_id: int,
    agent_tool_in: AgentToolUpdate,
) -> Any:
    """Update an agent-tool association."""
    agent_tool = await db.get(AgentTool, agent_tool_id)
    if not agent_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent-Tool association not found",
        )
    
    # Check permissions
    agent = await db.get(Agent, agent_tool.agent_id)
    if not current_user.is_superuser and agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update attributes
    for field, value in agent_tool_in.model_dump(exclude_unset=True).items():
        setattr(agent_tool, field, value)
    
    await db.commit()
    await db.refresh(agent_tool)
    return agent_tool


@router.delete("/agent-tools/{agent_tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_tool(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_tool_id: int,
) -> None:
    """Remove a tool from an agent."""
    agent_tool = await db.get(AgentTool, agent_tool_id)
    if not agent_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent-Tool association not found",
        )
    
    # Check permissions
    agent = await db.get(Agent, agent_tool.agent_id)
    if not current_user.is_superuser and agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    await db.delete(agent_tool)
    await db.commit() 