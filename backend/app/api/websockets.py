"""WebSocket live event stream for real-time dashboard updates."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected dashboard clients
_clients: list[WebSocket] = []


async def broadcast_event(event: dict):
    """Broadcast an event to all connected WebSocket clients."""
    if not _clients:
        return
    message = json.dumps(event)
    disconnected = []
    for client in _clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client)
    for client in disconnected:
        try:
            _clients.remove(client)
        except ValueError:
            pass


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live event streaming."""
    await websocket.accept()
    _clients.append(websocket)
    try:
        while True:
            # Keep connection alive; clients don't send data
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        try:
            _clients.remove(websocket)
        except ValueError:
            pass
