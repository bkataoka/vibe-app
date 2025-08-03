from fastapi import APIRouter

from api.v1.endpoints import auth, agents, tools, executions, websockets

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(websockets.router, tags=["websockets"]) 