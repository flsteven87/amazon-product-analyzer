"""Simple WebSocket implementation using FastAPI native WebSocket support."""

from typing import Dict, Set, Optional, Any
from uuid import UUID
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import logger


class SimpleWebSocketManager:
    """Simple WebSocket manager using FastAPI's native WebSocket support."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_subscribers: Dict[str, Set[str]] = {}  # task_id -> set of connection_ids
        self.enabled = True
        logger.info("Simple WebSocket manager initialized")

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            logger.info(f"WebSocket connection established: {connection_id}")
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            raise

    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
            # Remove from all task subscriptions
            for task_id in list(self.task_subscribers.keys()):
                self.task_subscribers[task_id].discard(connection_id)
                if not self.task_subscribers[task_id]:
                    del self.task_subscribers[task_id]
            
            logger.info(f"WebSocket connection removed: {connection_id}")

    def subscribe_to_task(self, connection_id: str, task_id: str):
        """Subscribe a connection to task updates."""
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        self.task_subscribers[task_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to task {task_id}")

    def unsubscribe_from_task(self, connection_id: str, task_id: str):
        """Unsubscribe a connection from task updates."""
        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(connection_id)
            if not self.task_subscribers[task_id]:
                del self.task_subscribers[task_id]
        logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                logger.debug(f"Sending message to {connection_id}: {message.get('type', 'unknown')}")
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Message sent successfully to {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                logger.error(f"WebSocket state: {websocket.client_state if 'websocket' in locals() else 'unknown'}")
                # Remove broken connection
                self.disconnect(connection_id)

    async def broadcast_to_task(self, message: dict, task_id: str):
        """Broadcast a message to all connections subscribed to a task."""
        if task_id not in self.task_subscribers:
            logger.warning(f"❌ No subscribers found for task {task_id}")
            return
            
        subscriber_count = len(self.task_subscribers[task_id])
        logger.info(f"📡 Broadcasting to {subscriber_count} subscribers for task {task_id}")
        
        disconnected_connections = []
        for connection_id in self.task_subscribers[task_id].copy():
            try:
                if connection_id not in self.active_connections:
                    logger.warning(f"⚠️ Connection {connection_id} not in active connections")
                    disconnected_connections.append(connection_id)
                    continue
                    
                await self.send_personal_message(message, connection_id)
                logger.debug(f"✅ Message sent to {connection_id}")
            except Exception as e:
                logger.error(f"💥 Failed to broadcast to {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            logger.warning(f"🧹 Cleaning up disconnected connection: {connection_id}")
            self.disconnect(connection_id)

    async def emit_progress_update(
        self, 
        task_id: str, 
        progress: int, 
        status: str, 
        agent_name: Optional[str] = None, 
        message: Optional[str] = None
    ):
        """Emit progress update to connections subscribed to a task."""
        update_data = {
            'type': 'progress_update',
            'task_id': task_id,
            'progress': progress,
            'status': status
        }
        
        if agent_name:
            update_data['agent_name'] = agent_name
        if message:
            update_data['message'] = message
        
        logger.info(f"🔄 Emitting progress update for task {task_id}: {progress}% (status: {status})")
        logger.info(f"📊 Active connections: {len(self.active_connections)}, Task subscribers: {len(self.task_subscribers.get(task_id, []))}")
        
        await self.broadcast_to_task(update_data, task_id)
        logger.info(f"✅ Progress update broadcast completed for task {task_id}")

    async def emit_agent_status(
        self, 
        task_id: str, 
        agent_name: str, 
        status: str, 
        message: Optional[str] = None
    ):
        """Emit agent status update."""
        status_data = {
            'type': 'agent_status',
            'agent_name': agent_name,
            'status': status,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        if message:
            status_data['message'] = message
        
        await self.broadcast_to_task(status_data, task_id)
        logger.debug(f"Emitted agent status for task {task_id}: {agent_name} - {status}")

    async def emit_analysis_complete(self, task_id: str, report_data: dict):
        """Emit analysis completion event."""
        complete_data = {
            'type': 'analysis_complete',
            'task_id': task_id,
            'report': report_data
        }
        
        await self.broadcast_to_task(complete_data, task_id)
        logger.info(f"Emitted analysis complete for task {task_id}")

    def get_stats(self):
        """Get WebSocket connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "task_subscriptions": {task_id: len(connections) for task_id, connections in self.task_subscribers.items()}
        }


# Global simple WebSocket manager instance
simple_ws_manager = SimpleWebSocketManager()