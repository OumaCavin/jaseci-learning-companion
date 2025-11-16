"""
Real-time WebSocket Implementation
Enterprise WebSocket server for Jaseci Learning Companion

Handles real-time progress updates, agent communications, and live UI updates.
Supports WebSocket connections with authentication, room management, and broadcasting.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import jwt
import redis.asyncio as redis
import uvicorn
from fastapi import (
    WebSocket, WebSocketDisconnect, Depends, HTTPException, status
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security
SECRET_KEY = "your-secret-key-here"  # In production, load from environment
ALGORITHM = "HS256"
security = HTTPBearer()


# Message Types and Data Models
class MessageType:
    """WebSocket message types"""
    AUTHENTICATE = "authenticate"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PROGRESS_UPDATE = "progress_update"
    CODE_SUBMISSION = "code_submission"
    QUALITY_ASSESSMENT = "quality_assessment"
    AGENT_RESPONSE = "agent_response"
    NOTIFICATION = "notification"
    SYSTEM_ALERT = "system_alert"
    ERROR = "error"
    BROADCAST = "broadcast"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    message_id: str
    type: str
    sender: str
    recipient: Optional[str] = None
    room: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    priority: int = 2  # 1=high, 2=normal, 3=low
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    user_id: str
    websocket: WebSocket
    rooms: Set[str] = field(default_factory=set)
    authenticated: bool = False
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    bytes_sent: int = 0
    client_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Room:
    """Chat room/channel for message broadcasting"""
    room_id: str
    name: str
    description: Optional[str] = None
    members: Set[str] = field(default_factory=set)
    moderators: Set[str] = field(default_factory=set)
    is_private: bool = False
    max_members: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    settings: Dict[str, Any] = field(default_factory=dict)


class MessageValidator:
    """Validates WebSocket messages"""
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """Validate message structure"""
        required_fields = ['type', 'message_id', 'sender']
        
        for field in required_fields:
            if field not in message:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Validate message type
        valid_types = [
            MessageType.AUTHENTICATE, MessageType.HEARTBEAT, MessageType.SUBSCRIBE,
            MessageType.UNSUBSCRIBE, MessageType.PROGRESS_UPDATE, MessageType.CODE_SUBMISSION,
            MessageType.QUALITY_ASSESSMENT, MessageType.AGENT_RESPONSE, MessageType.NOTIFICATION,
            MessageType.SYSTEM_ALERT, MessageType.ERROR, MessageType.BROADCAST
        ]
        
        if message['type'] not in valid_types:
            logger.error(f"Invalid message type: {message['type']}")
            return False
            
        return True
        
    @staticmethod
    def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize message payload to prevent injection attacks"""
        # Remove potentially dangerous fields
        dangerous_fields = ['__proto__', 'constructor', 'prototype']
        
        def clean_dict(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: clean_dict(v) for k, v in obj.items() if k not in dangerous_fields}
            elif isinstance(obj, list):
                return [clean_dict(item) for item in obj]
            else:
                return obj
                
        return clean_dict(payload)


class MessageQueue:
    """Priority message queue for reliable delivery"""
    
    def __init__(self, max_size: int = 1000):
        self.queues: Dict[int, deque] = {
            1: deque(maxlen=max_size),  # High priority
            2: deque(maxlen=max_size),  # Normal priority
            3: deque(maxlen=max_size),  # Low priority
        }
        self.lock = asyncio.Lock()
        
    async def put(self, message: WebSocketMessage):
        """Add message to queue"""
        async with self.lock:
            queue = self.queues[message.priority]
            queue.append(message)
            
    async def get(self) -> Optional[WebSocketMessage]:
        """Get highest priority message"""
        async with self.lock:
            # Try high priority first, then normal, then low
            for priority in [1, 2, 3]:
                if self.queues[priority]:
                    return self.queues[priority].popleft()
            return None
            
    async def size(self) -> int:
        """Get total queue size"""
        async with self.lock:
            return sum(len(queue) for queue in self.queues.values())


class WebSocketManager:
    """Enterprise WebSocket connection manager"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.rooms: Dict[str, Room] = {}
        self.message_queue = MessageQueue()
        self.heartbeat_interval = 30  # seconds
        self.message_cleanup_interval = 60  # seconds
        
        # Default rooms
        self._initialize_default_rooms()
        
    def _initialize_default_rooms(self):
        """Initialize default rooms"""
        default_rooms = [
            Room("global", "Global Chat", "Public chat for all users"),
            Room("system", "System", "System notifications and alerts"),
            Room("progress", "Progress Updates", "Learning progress updates"),
            Room("agents", "Agent Communications", "Agent system communications"),
        ]
        
        for room in default_rooms:
            self.rooms[room.room_id] = room
            
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        client_info: Dict[str, Any] = None
    ) -> str:
        """Accept WebSocket connection"""
        connection_id = str(uuid4())
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
            client_info=client_info or {}
        )
        
        # Store connection
        self.connections[connection_id] = connection_info
        self.user_connections[user_id].add(connection_id)
        
        # Accept connection
        await websocket.accept()
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            message_id=str(uuid4()),
            type=MessageType.BROADCAST,
            sender="system",
            payload={
                "message": "Welcome to Jaseci Learning Companion",
                "connection_id": connection_id,
                "user_id": user_id,
                "server_time": datetime.now(timezone.utc).isoformat(),
                "available_rooms": list(self.rooms.keys())
            }
        )
        
        await self.send_message_to_connection(connection_id, welcome_message)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id
        
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket"""
        if connection_id not in self.connections:
            return
            
        connection_info = self.connections[connection_id]
        user_id = connection_info.user_id
        
        # Remove from rooms
        for room_id in list(connection_info.rooms):
            await self.leave_room(connection_id, room_id)
            
        # Remove from user connections
        self.user_connections[user_id].discard(connection_id)
        if not self.user_connections[user_id]:
            del self.user_connections[user_id]
            
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
        
    async def authenticate_connection(self, connection_id: str, token: str) -> bool:
        """Authenticate WebSocket connection"""
        try:
            # Verify JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = str(payload.get("sub"))
            
            if connection_id in self.connections:
                self.connections[connection_id].authenticated = True
                
                # Join user to their private room
                user_room = f"user_{user_id}"
                await self.join_room(connection_id, user_room)
                
                # Send authentication success
                auth_message = WebSocketMessage(
                    message_id=str(uuid4()),
                    type=MessageType.AUTHENTICATE,
                    sender="system",
                    recipient=user_id,
                    payload={
                        "status": "authenticated",
                        "user_id": user_id,
                        "permissions": payload.get("permissions", [])
                    }
                )
                
                await self.send_message_to_connection(connection_id, auth_message)
                
                logger.info(f"WebSocket authenticated: {connection_id} for user {user_id}")
                return True
                
        except jwt.JWTError as e:
            logger.error(f"Authentication failed for {connection_id}: {e}")
            
        return False
        
    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """Join user to a room"""
        if connection_id not in self.connections:
            return False
            
        if room_id not in self.rooms:
            # Create room if it doesn't exist
            self.rooms[room_id] = Room(room_id, room_id)
            
        connection_info = self.connections[connection_id]
        room = self.rooms[room_id]
        
        # Check room limits
        if room.max_members and len(room.members) >= room.max_members:
            await self.send_error(connection_id, f"Room {room_id} is full")
            return False
            
        # Add to room
        connection_info.rooms.add(room_id)
        room.members.add(connection_info.user_id)
        
        # Confirm join
        join_message = WebSocketMessage(
            message_id=str(uuid4()),
            type=MessageType.SUBSCRIBE,
            sender="system",
            recipient=connection_info.user_id,
            payload={
                "room_id": room_id,
                "status": "joined",
                "room_info": {
                    "name": room.name,
                    "member_count": len(room.members)
                }
            }
        )
        
        await self.send_message_to_connection(connection_id, join_message)
        
        logger.info(f"User {connection_info.user_id} joined room {room_id}")
        return True
        
    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """Leave a room"""
        if connection_id not in self.connections or room_id not in self.rooms:
            return False
            
        connection_info = self.connections[connection_id]
        room = self.rooms[room_id]
        
        # Remove from room
        connection_info.rooms.discard(room_id)
        room.members.discard(connection_info.user_id)
        
        # Confirm leave
        leave_message = WebSocketMessage(
            message_id=str(uuid4()),
            type=MessageType.UNSUBSCRIBE,
            sender="system",
            recipient=connection_info.user_id,
            payload={
                "room_id": room_id,
                "status": "left"
            }
        )
        
        await self.send_message_to_connection(connection_id, leave_message)
        
        logger.info(f"User {connection_info.user_id} left room {room_id}")
        return True
        
    async def send_message_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return
            
        connection_info = self.connections[connection_id]
        
        try:
            # Convert message to JSON
            message_dict = {
                "message_id": message.message_id,
                "type": message.type,
                "sender": message.sender,
                "recipient": message.recipient,
                "room": message.room,
                "payload": message.payload,
                "timestamp": message.timestamp.isoformat()
            }
            
            # Send message
            await connection_info.websocket.send_text(json.dumps(message_dict))
            
            # Update stats
            connection_info.message_count += 1
            connection_info.bytes_sent += len(json.dumps(message_dict))
            
        except WebSocketDisconnect:
            # Connection closed, clean up
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            
    async def send_message_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections for a user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_message_to_connection(connection_id, message)
                
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage):
        """Broadcast message to all users in a room"""
        if room_id not in self.rooms:
            return
            
        room = self.rooms[room_id]
        message.room = room_id
        
        for user_id in room.members:
            await self.send_message_to_user(user_id, message)
            
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected users"""
        for user_id in self.user_connections.keys():
            await self.send_message_to_user(user_id, message)
            
    async def send_error(self, connection_id: str, error_message: str):
        """Send error message"""
        error_msg = WebSocketMessage(
            message_id=str(uuid4()),
            type=MessageType.ERROR,
            sender="system",
            payload={
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await self.send_message_to_connection(connection_id, error_msg)
        
    async def handle_heartbeat(self, connection_id: str):
        """Handle heartbeat from client"""
        if connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = datetime.now(timezone.utc)
            
    async def send_heartbeat(self, connection_id: str):
        """Send heartbeat to client"""
        heartbeat_msg = WebSocketMessage(
            message_id=str(uuid4()),
            type=MessageType.HEARTBEAT,
            sender="system",
            payload={
                "server_time": datetime.now(timezone.utc).isoformat(),
                "connection_id": connection_id
            }
        )
        
        await self.send_message_to_connection(connection_id, heartbeat_msg)
        
    async def cleanup_stale_connections(self):
        """Remove stale connections"""
        current_time = datetime.now(timezone.utc)
        stale_threshold = 60  # seconds
        
        stale_connections = []
        for connection_id, connection_info in self.connections.items():
            time_since_heartbeat = (current_time - connection_info.last_heartbeat).total_seconds()
            if time_since_heartbeat > stale_threshold:
                stale_connections.append(connection_id)
                
        for connection_id in stale_connections:
            logger.info(f"Cleaning up stale connection: {connection_id}")
            await self.disconnect(connection_id)
            
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.connections)
        total_users = len(self.user_connections)
        total_rooms = len(self.rooms)
        
        # Calculate room statistics
        room_stats = {}
        for room_id, room in self.rooms.items():
            room_stats[room_id] = {
                "name": room.name,
                "member_count": len(room.members),
                "is_private": room.is_private
            }
            
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_rooms": total_rooms,
            "rooms": room_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class WebSocketServer:
    """WebSocket server with FastAPI integration"""
    
    def __init__(self, connection_string: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(connection_string)
        self.manager = WebSocketManager(self.redis_client)
        self.background_tasks: Set[asyncio.Task] = set()
        
    async def start_background_tasks(self):
        """Start background tasks"""
        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.background_tasks.add(heartbeat_task)
        
        # Connection cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.background_tasks.add(cleanup_task)
        
        # Message processing task
        message_task = asyncio.create_task(self._message_queue_loop())
        self.background_tasks.add(message_task)
        
        logger.info("WebSocket background tasks started")
        
    async def stop_background_tasks(self):
        """Stop background tasks"""
        for task in self.background_tasks:
            task.cancel()
            
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        logger.info("WebSocket background tasks stopped")
        
    async def _heartbeat_loop(self):
        """Background task for sending heartbeats"""
        while True:
            try:
                # Send heartbeats to all connections
                for connection_id in list(self.manager.connections.keys()):
                    await self.manager.send_heartbeat(connection_id)
                    
                await asyncio.sleep(self.manager.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
                
    async def _cleanup_loop(self):
        """Background task for cleaning up stale connections"""
        while True:
            try:
                await self.manager.cleanup_stale_connections()
                await asyncio.sleep(self.manager.message_cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
                
    async def _message_queue_loop(self):
        """Background task for processing message queue"""
        while True:
            try:
                message = await self.manager.message_queue.get()
                if message:
                    # Process queued message
                    if message.recipient:
                        await self.manager.send_message_to_user(message.recipient, message)
                    elif message.room:
                        await self.manager.broadcast_to_room(message.room, message)
                    else:
                        await self.manager.broadcast_to_all(message)
                        
                await asyncio.sleep(0.1)  # Small delay
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message queue loop: {e}")
                await asyncio.sleep(1)


# FastAPI WebSocket Endpoint
async def websocket_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = None,
    user_id: Optional[str] = None,
    server: WebSocketServer = None
):
    """WebSocket endpoint with authentication"""
    connection_id = None
    
    try:
        # Get user identification
        if not user_id:
            # Try to get from token
            if token:
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    user_id = str(payload.get("sub"))
                except jwt.JWTError:
                    await websocket.close(code=4401, reason="Invalid token")
                    return
            else:
                # Use client-provided ID (in production, use proper auth)
                user_id = f"anonymous_{str(uuid4())[:8]}"
                
        # Connect
        connection_id = await server.manager.connect(
            websocket, 
            user_id,
            {
                "user_agent": websocket.headers.get("user-agent", ""),
                "origin": websocket.headers.get("origin", ""),
                "remote_addr": websocket.client.host if websocket.client else "unknown"
            }
        )
        
        # Authenticate if token provided
        if token:
            await server.manager.authenticate_connection(connection_id, token)
            
        # Start message handling loop
        while True:
            # Receive message
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message
                if not MessageValidator.validate_message(message_data):
                    await server.manager.send_error(connection_id, "Invalid message format")
                    continue
                    
                # Process message based on type
                await server._handle_message(connection_id, message_data)
                
            except json.JSONDecodeError:
                await server.manager.send_error(connection_id, "Invalid JSON")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await server.manager.send_error(connection_id, "Internal server error")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id:
            await server.manager.disconnect(connection_id)


async def _handle_message(self, connection_id: str, message_data: Dict[str, Any]):
    """Handle incoming WebSocket message"""
    message_type = message_data.get("type")
    
    try:
        if message_type == MessageType.AUTHENTICATE:
            token = message_data.get("payload", {}).get("token")
            await self.manager.authenticate_connection(connection_id, token)
            
        elif message_type == MessageType.HEARTBEAT:
            await self.manager.handle_heartbeat(connection_id)
            
        elif message_type == MessageType.SUBSCRIBE:
            room_id = message_data.get("payload", {}).get("room_id")
            if room_id:
                await self.manager.join_room(connection_id, room_id)
                
        elif message_type == MessageType.UNSUBSCRIBE:
            room_id = message_data.get("payload", {}).get("room_id")
            if room_id:
                await self.manager.leave_room(connection_id, room_id)
                
        elif message_type in [
            MessageType.PROGRESS_UPDATE, MessageType.CODE_SUBMISSION, 
            MessageType.QUALITY_ASSESSMENT, MessageType.AGENT_RESPONSE,
            MessageType.NOTIFICATION, MessageType.SYSTEM_ALERT
        ]:
            # Create WebSocket message
            ws_message = WebSocketMessage(
                message_id=message_data.get("message_id", str(uuid4())),
                type=message_type,
                sender=message_data.get("sender"),
                recipient=message_data.get("recipient"),
                room=message_data.get("room"),
                payload=MessageValidator.sanitize_payload(message_data.get("payload", {}))
            )
            
            # Route message
            if ws_message.recipient:
                await self.manager.send_message_to_user(ws_message.recipient, ws_message)
            elif ws_message.room:
                await self.manager.broadcast_to_room(ws_message.room, ws_message)
            else:
                await self.manager.broadcast_to_all(ws_message)
                
        else:
            await self.manager.send_error(connection_id, f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await self.manager.send_error(connection_id, "Message handling error")


# Helper functions for sending specific types of messages
async def send_progress_update(server: WebSocketServer, user_id: str, progress_data: Dict[str, Any]):
    """Send progress update to user"""
    message = WebSocketMessage(
        message_id=str(uuid4()),
        type=MessageType.PROGRESS_UPDATE,
        sender="system",
        recipient=user_id,
        payload={
            "lesson_id": progress_data.get("lesson_id"),
            "progress_percentage": progress_data.get("progress_percentage"),
            "status": progress_data.get("status"),
            "time_spent": progress_data.get("time_spent"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    await server.manager.send_message_to_user(user_id, message)


async def send_quality_assessment(server: WebSocketServer, user_id: str, assessment_data: Dict[str, Any]):
    """Send quality assessment results"""
    message = WebSocketMessage(
        message_id=str(uuid4()),
        type=MessageType.QUALITY_ASSESSMENT,
        sender="quality_assessor",
        recipient=user_id,
        payload={
            "submission_id": assessment_data.get("submission_id"),
            "overall_score": assessment_data.get("overall_score"),
            "detailed_scores": assessment_data.get("detailed_scores", {}),
            "feedback": assessment_data.get("feedback", []),
            "recommendations": assessment_data.get("recommendations", []),
            "processing_time": assessment_data.get("processing_time"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    await server.manager.send_message_to_user(user_id, message)


async def broadcast_system_alert(server: WebSocketServer, alert_data: Dict[str, Any]):
    """Broadcast system alert to all users"""
    message = WebSocketMessage(
        message_id=str(uuid4()),
        type=MessageType.SYSTEM_ALERT,
        sender="system",
        payload={
            "alert_type": alert_data.get("alert_type"),
            "severity": alert_data.get("severity", "info"),
            "title": alert_data.get("title"),
            "message": alert_data.get("message"),
            "action_required": alert_data.get("action_required", False),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    await server.manager.broadcast_to_all(message)


# Application factory
def create_websocket_server(connection_string: str = "redis://localhost:6379") -> WebSocketServer:
    """Create and configure WebSocket server"""
    return WebSocketServer(connection_string)


if __name__ == "__main__":
    # Run WebSocket server standalone
    import uvicorn
    
    server = create_websocket_server()
    
    uvicorn.run(
        "websocket_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )