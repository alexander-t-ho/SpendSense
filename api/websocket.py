"""WebSocket support for real-time consent updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from datetime import datetime
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store connections by user_id (for user-specific updates)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store operator/admin connections (for recommendation updates)
        self.operator_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection and store it."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections.get(user_id, set()))}")
    
    async def connect_operator(self, websocket: WebSocket):
        """Accept a WebSocket connection for operators/admins."""
        await websocket.accept()
        self.operator_connections.add(websocket)
        print(f"Operator WebSocket connected. Total operator connections: {len(self.operator_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"WebSocket disconnected for user {user_id}")
    
    def disconnect_operator(self, websocket: WebSocket):
        """Remove an operator WebSocket connection."""
        self.operator_connections.discard(websocket)
        print(f"Operator WebSocket disconnected. Total operator connections: {len(self.operator_connections)}")
    
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
    
    async def broadcast_to_operators(self, message: dict):
        """Broadcast a message to all operator connections."""
        disconnected = set()
        for connection in self.operator_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to operator: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect_operator(conn)
    
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
    
    async def broadcast_recommendation_update(self, recommendation_id: str, action: str, recommendation_data: dict):
        """Broadcast recommendation status update to all operator connections."""
        message = {
            "type": "recommendation_update",
            "recommendation_id": recommendation_id,
            "action": action,  # "approved", "rejected", "flagged"
            "data": recommendation_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_operators(message)
    
    async def broadcast_subscription_cancellation(self, user_id: str, merchant_name: str, cancelled: bool):
        """Broadcast subscription cancellation/uncancellation to user's connections."""
        message = {
            "type": "subscription_cancellation",
            "user_id": user_id,
            "merchant_name": merchant_name,
            "cancelled": cancelled,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


