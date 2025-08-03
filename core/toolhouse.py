from typing import Any, Dict, Optional
import httpx
from fastapi import HTTPException

from core.config import settings


class ToolhouseClient:
    """Client for interacting with the Toolhouse API."""

    def __init__(self) -> None:
        self.base_url = settings.TOOLHOUSE_BASE_URL.rstrip('/')
        self.api_key = settings.TOOLHOUSE_API_KEY
        if not self.api_key:
            raise ValueError("TOOLHOUSE_API_KEY must be set")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Toolhouse API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=e.response.status_code if hasattr(e, 'response') else 500,
                    detail=str(e),
                )

    async def register_agent(self, name: str, configuration: Dict[str, Any]) -> str:
        """Register a new agent with Toolhouse."""
        data = {
            "name": name,
            "configuration": configuration,
        }
        response = await self._make_request("POST", "/agents", data)
        return response["agent_id"]

    async def update_agent(
        self,
        agent_id: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing agent's configuration."""
        data = {"configuration": configuration}
        return await self._make_request("PUT", f"/agents/{agent_id}", data)

    async def register_tool(
        self,
        name: str,
        schema: Dict[str, Any],
        configuration: Dict[str, Any],
    ) -> str:
        """Register a new tool with Toolhouse."""
        data = {
            "name": name,
            "schema": schema,
            "configuration": configuration,
        }
        response = await self._make_request("POST", "/tools", data)
        return response["tool_id"]

    async def update_tool(
        self,
        tool_id: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing tool's configuration."""
        data = {"configuration": configuration}
        return await self._make_request("PUT", f"/tools/{tool_id}", data)

    async def start_execution(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
    ) -> str:
        """Start a new agent execution."""
        data = {"input_data": input_data}
        response = await self._make_request("POST", f"/agents/{agent_id}/execute", data)
        return response["execution_id"]

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of an execution."""
        return await self._make_request("GET", f"/executions/{execution_id}")

    async def stop_execution(self, execution_id: str) -> Dict[str, Any]:
        """Stop an ongoing execution."""
        return await self._make_request("POST", f"/executions/{execution_id}/stop")


# Create a global client instance
toolhouse_client = ToolhouseClient() 