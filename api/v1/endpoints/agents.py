from typing import Any, List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.v1.deps import AsyncSessionDep, CurrentUser
from core.toolhouse import toolhouse_client
from models.agent import Agent
from schemas.agent import (
    Agent as AgentSchema,
    AgentCreate,
    AgentUpdate,
    AgentWithTools,
    AgentComplete,
)

router = APIRouter()


@router.get("/", response_model=List[AgentSchema])
async def list_agents(
    db: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all agents for current user."""
    query = select(Agent).where(Agent.user_id == current_user.id)
    if not current_user.is_superuser:
        query = query.where(Agent.user_id == current_user.id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AgentSchema)
async def create_agent(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_in: AgentCreate,
) -> Any:
    """Create a new agent."""
    try:
        # Register agent with Toolhouse
        toolhouse_agent_id = await toolhouse_client.register_agent(
            name=agent_in.name,
            configuration=agent_in.configuration,
        )
        
        # Create agent in database
        agent = Agent(
            **agent_in.model_dump(),
            user_id=current_user.id,
            toolhouse_agent_id=toolhouse_agent_id,
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create agent: {str(e)}",
        )


@router.get("/{agent_id}", response_model=AgentComplete)
async def get_agent(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_id: int,
) -> Any:
    """Get agent by ID."""
    query = (
        select(Agent)
        .where(Agent.id == agent_id)
        .options(
            selectinload(Agent.agent_tools).selectinload(Agent.tool),
            selectinload(Agent.executions),
        )
    )
    if not current_user.is_superuser:
        query = query.where(Agent.user_id == current_user.id)
    
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent


@router.put("/{agent_id}", response_model=AgentSchema)
async def update_agent(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_id: int,
    agent_in: AgentUpdate,
) -> Any:
    """Update an agent."""
    agent = await db.get(Agent, agent_id)
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
    
    try:
        # Update agent in Toolhouse if configuration changed
        if agent_in.configuration is not None and agent.toolhouse_agent_id:
            await toolhouse_client.update_agent(
                agent_id=agent.toolhouse_agent_id,
                configuration=agent_in.configuration,
            )
        
        # Update agent attributes
        for field, value in agent_in.model_dump(exclude_unset=True).items():
            setattr(agent, field, value)
        
        await db.commit()
        await db.refresh(agent)
        return agent
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update agent: {str(e)}",
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    *,
    db: AsyncSessionDep,
    current_user: CurrentUser,
    agent_id: int,
) -> None:
    """Delete an agent."""
    agent = await db.get(Agent, agent_id)
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
    
    # Note: We don't delete the agent from Toolhouse as it might be used by other systems
    # or needed for historical data
    
    await db.delete(agent)
    await db.commit() 