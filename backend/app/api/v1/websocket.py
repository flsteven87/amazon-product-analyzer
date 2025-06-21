"""WebSocket API endpoints."""

import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket_simple import simple_ws_manager
from app.core.logging import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    connection_id = str(uuid.uuid4())
    
    try:
        await simple_ws_manager.connect(websocket, connection_id)
        logger.info(f"WebSocket client connected: {connection_id}")
        
        # Send welcome message
        await simple_ws_manager.send_personal_message(
            {"type": "connected", "connection_id": connection_id}, 
            connection_id
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "join_task":
                    task_id = message.get("task_id")
                    if task_id:
                        simple_ws_manager.subscribe_to_task(connection_id, task_id)
                        await simple_ws_manager.send_personal_message(
                            {"type": "joined_task", "task_id": task_id}, 
                            connection_id
                        )
                        logger.info(f"Client {connection_id} joined task {task_id}")
                
                elif message_type == "leave_task":
                    task_id = message.get("task_id")
                    if task_id:
                        simple_ws_manager.unsubscribe_from_task(connection_id, task_id)
                        await simple_ws_manager.send_personal_message(
                            {"type": "left_task", "task_id": task_id}, 
                            connection_id
                        )
                        logger.info(f"Client {connection_id} left task {task_id}")
                
                elif message_type == "ping":
                    await simple_ws_manager.send_personal_message(
                        {"type": "pong"}, 
                        connection_id
                    )
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message from {connection_id}: {data}")
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        simple_ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "websocket_enabled": True,
        "stats": simple_ws_manager.get_stats()
    }