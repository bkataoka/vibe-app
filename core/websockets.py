from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # All active connections
        self.active_connections: Set[WebSocket] = set()
        # Connections by user_id
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        # Connections subscribed to specific executions
        self.execution_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        execution_id: Optional[int] = None,
    ) -> None:
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Add to execution connections if specified
        if execution_id is not None:
            if execution_id not in self.execution_connections:
                self.execution_connections[execution_id] = set()
            self.execution_connections[execution_id].add(websocket)

    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: int,
        execution_id: Optional[int] = None,
    ) -> None:
        """Disconnect a WebSocket client."""
        self.active_connections.discard(websocket)
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from execution connections
        if execution_id is not None and execution_id in self.execution_connections:
            self.execution_connections[execution_id].discard(websocket)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]

    async def broadcast_to_user(
        self,
        user_id: int,
        message_type: str,
        data: Any,
    ) -> None:
        """Broadcast a message to all connections of a specific user."""
        if user_id not in self.user_connections:
            return
        
        message = {
            "type": message_type,
            "data": data,
        }
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                await self.disconnect(connection, user_id)

    async def broadcast_to_execution(
        self,
        execution_id: int,
        message_type: str,
        data: Any,
    ) -> None:
        """Broadcast a message to all connections watching a specific execution."""
        if execution_id not in self.execution_connections:
            return
        
        message = {
            "type": message_type,
            "data": data,
        }
        
        for connection in self.execution_connections[execution_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to execution {execution_id}: {e}")
                # Get user_id from connection (you might need to store this information)
                await self.disconnect(connection, 0, execution_id)

    async def broadcast_system_message(
        self,
        message_type: str,
        data: Any,
    ) -> None:
        """Broadcast a message to all active connections."""
        message = {
            "type": message_type,
            "data": data,
        }
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting system message: {e}")
                # Clean up failed connection
                self.active_connections.discard(connection)


# Create a global connection manager instance
manager = ConnectionManager() 