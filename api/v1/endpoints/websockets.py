from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from jose import jwt, JWTError

from core.config import settings
from core.websockets import manager
from schemas.user import TokenPayload

router = APIRouter()


async def get_user_id_from_token(token: str) -> int:
    """Get user ID from JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
        return token_data.sub
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
) -> None:
    """General WebSocket endpoint for user updates."""
    try:
        user_id = await get_user_id_from_token(token)
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # Wait for messages (can be used for ping/pong or client requests)
                data = await websocket.receive_json()
                # Handle client messages if needed
                await websocket.send_json({"status": "received"})
                
        except WebSocketDisconnect:
            await manager.disconnect(websocket, user_id)
            
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)


@router.websocket("/ws/executions/{execution_id}")
async def execution_websocket_endpoint(
    websocket: WebSocket,
    execution_id: int,
    token: str,
) -> None:
    """WebSocket endpoint for specific execution updates."""
    try:
        user_id = await get_user_id_from_token(token)
        await manager.connect(websocket, user_id, execution_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "execution_id": execution_id,
                "message": "Connected to execution updates"
            }
        })
        
        try:
            while True:
                # Wait for messages
                data = await websocket.receive_json()
                # Handle client messages if needed
                await websocket.send_json({"status": "received"})
                
        except WebSocketDisconnect:
            await manager.disconnect(websocket, user_id, execution_id)
            
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION) 