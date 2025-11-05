"""WebSocket support for real-time consent updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection and store it."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections.get(user_id, set()))}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to all connections for a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_consent_update(self, user_id: str, consented: bool, consent_data: dict):
        """Broadcast consent status update to user's connections."""
        message = {
            "type": "consent_update",
            "user_id": user_id,
            "consented": consented,
            "data": consent_data,
            "timestamp": consent_data.get("consented_at") or consent_data.get("revoked_at")
        }
        await self.send_personal_message(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


