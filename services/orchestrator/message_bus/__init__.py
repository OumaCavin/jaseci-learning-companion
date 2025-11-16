#!/usr/bin/env python3
"""
Jaseci Learning Companion - Message Bus
Inter-agent communication and message routing

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    BROADCAST = "broadcast"
    ERROR = "error"

class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Message:
    """Message data structure"""
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]
    payload: Dict[str, Any]
    priority: MessagePriority
    timestamp: datetime
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None

class MessageBus:
    """Enterprise message bus for inter-agent communication"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.subscribers: Dict[str, Set[Callable]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue: List[Message] = []
        self._lock = asyncio.Lock()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
    
    async def initialize(self, redis_url: str = None):
        """Initialize message bus"""
        try:
            if not self.redis_client:
                if redis_url:
                    self.redis_client = redis.from_url(redis_url)
                else:
                    self.redis_client = redis.from_url("redis://localhost:6379/0")
            
            # Test Redis connection
            await self.redis_client.ping()
            
            # Start message processor
            await self.start()
            
            logger.info("Message bus initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing message bus: {e}")
            raise
    
    async def start(self):
        """Start message bus"""
        if not self._running:
            self._running = True
            self._processor_task = asyncio.create_task(self._process_messages())
            logger.info("Message bus started")
    
    async def stop(self):
        """Stop message bus"""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Message bus stopped")
    
    async def send_message(self, message: Message) -> str:
        """Send message"""
        try:
            message_id = message.message_id or str(uuid.uuid4())
            message.message_id = message_id
            
            # Store in Redis for persistence
            await self._store_message_redis(message)
            
            # Add to local queue for immediate processing
            async with self._lock:
                self.message_queue.append(message)
            
            logger.debug(f"Message sent: {message_id} from {message.sender_id} to {message.recipient_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def send_direct_message(self, sender_id: str, recipient_id: str, 
                                 payload: Dict[str, Any], 
                                 message_type: MessageType = MessageType.TASK_REQUEST,
                                 priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send direct message to specific agent"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            priority=priority,
            timestamp=datetime.utcnow()
        )
        
        return await self.send_message(message)
    
    async def broadcast_message(self, sender_id: str, payload: Dict[str, Any],
                               message_type: MessageType = MessageType.BROADCAST,
                               priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Broadcast message to all subscribers"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=sender_id,
            recipient_id=None,  # Broadcast
            payload=payload,
            priority=priority,
            timestamp=datetime.utcnow()
        )
        
        return await self.send_message(message)
    
    async def subscribe(self, agent_id: str, handler: Callable[[Message], None]):
        """Subscribe to messages for agent"""
        async with self._lock:
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = set()
            self.subscribers[agent_id].add(handler)
        
        logger.info(f"Agent {agent_id} subscribed to messages")
    
    async def unsubscribe(self, agent_id: str, handler: Callable[[Message], None] = None):
        """Unsubscribe from messages"""
        async with self._lock:
            if agent_id in self.subscribers:
                if handler:
                    self.subscribers[agent_id].discard(handler)
                    if not self.subscribers[agent_id]:
                        del self.subscribers[agent_id]
                else:
                    del self.subscribers[agent_id]
        
        logger.info(f"Agent {agent_id} unsubscribed from messages")
    
    async def register_handler(self, message_type: MessageType, handler: Callable[[Message], None]):
        """Register global message handler"""
        self.message_handlers[message_type.value] = handler
        logger.info(f"Registered handler for message type: {message_type.value}")
    
    async def get_message_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get message history for agent"""
        try:
            # Get from Redis
            messages = await self.redis_client.lrange(f"message_history:{agent_id}", 0, limit - 1)
            history = []
            
            for msg_data in messages:
                try:
                    message_dict = json.loads(msg_data)
                    history.append(message_dict)
                except json.JSONDecodeError:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting message history for {agent_id}: {e}")
            return []
    
    async def get_queue_size(self, agent_id: str = None) -> int:
        """Get message queue size"""
        try:
            if agent_id:
                # Get size of specific agent's queue
                queue_key = f"message_queue:{agent_id}"
                size = await self.redis_client.llen(queue_key)
                return size
            else:
                # Get total queue size
                total_size = 0
                async for key in self.redis_client.scan_iter(match="message_queue:*"):
                    size = await self.redis_client.llen(key)
                    total_size += size
                return total_size
                
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0
    
    async def clear_queue(self, agent_id: str) -> int:
        """Clear message queue for agent"""
        try:
            queue_key = f"message_queue:{agent_id}"
            size = await self.redis_client.llen(queue_key)
            await self.redis_client.delete(queue_key)
            
            logger.info(f"Cleared {size} messages from queue for {agent_id}")
            return size
            
        except Exception as e:
            logger.error(f"Error clearing queue for {agent_id}: {e}")
            return 0
    
    async def get_bus_metrics(self) -> Dict[str, Any]:
        """Get message bus metrics"""
        try:
            # Get subscriber count
            subscriber_count = len(self.subscribers)
            
            # Get queue sizes
            total_queue_size = 0
            agent_queue_sizes = {}
            
            async for key in self.redis_client.scan_iter(match="message_queue:*"):
                agent_id = key.replace("message_queue:", "")
                size = await self.redis_client.llen(key)
                agent_queue_sizes[agent_id] = size
                total_queue_size += size
            
            # Get message statistics
            today_messages = await self.redis_client.get("metrics:messages_today") or 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "subscribers": subscriber_count,
                "total_queue_size": total_queue_size,
                "agent_queues": agent_queue_sizes,
                "messages_today": int(today_messages),
                "handlers_registered": len(self.message_handlers)
            }
            
        except Exception as e:
            logger.error(f"Error getting bus metrics: {e}")
            return {}
    
    async def close(self):
        """Close message bus"""
        await self.stop()
        logger.info("Message bus closed")
    
    async def _process_messages(self):
        """Process messages from queue"""
        while self._running:
            try:
                # Process local queue
                async with self._lock:
                    if self.message_queue:
                        # Sort by priority
                        self.message_queue.sort(key=lambda x: self._get_priority_value(x.priority), reverse=True)
                        
                        message = self.message_queue.pop(0)
                    else:
                        message = None
                
                if message:
                    await self._deliver_message(message)
                else:
                    # Check Redis for pending messages
                    await self._check_redis_messages()
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_message(self, message: Message):
        """Deliver message to recipients"""
        try:
            # Check if message has expired
            if message.expires_at and datetime.utcnow() > message.expires_at:
                logger.debug(f"Message {message.message_id} expired, discarding")
                return
            
            delivered = False
            
            # Direct message to specific recipient
            if message.recipient_id and message.recipient_id in self.subscribers:
                delivered = True
                await self._notify_subscribers(message.recipient_id, message)
            
            # Broadcast message to all subscribers
            elif message.recipient_id is None:
                delivered = True
                for subscriber_id in self.subscribers:
                    await self._notify_subscribers(subscriber_id, message)
            
            # Call global message handlers
            handler = self.message_handlers.get(message.message_type.value)
            if handler:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            
            # Update metrics
            if delivered:
                await self._increment_message_metrics()
            
        except Exception as e:
            logger.error(f"Error delivering message {message.message_id}: {e}")
    
    async def _notify_subscribers(self, subscriber_id: str, message: Message):
        """Notify subscribers"""
        if subscriber_id in self.subscribers:
            handlers = self.subscribers[subscriber_id].copy()
            
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in subscriber handler for {subscriber_id}: {e}")
    
    async def _store_message_redis(self, message: Message):
        """Store message in Redis"""
        try:
            message_data = json.dumps(asdict(message), default=str)
            
            # Store in recipient's queue
            if message.recipient_id:
                queue_key = f"message_queue:{message.recipient_id}"
                await self.redis_client.lpush(queue_key, message_data)
                
                # Set expiry for the message
                if message.expires_at:
                    ttl = int((message.expires_at - datetime.utcnow()).total_seconds())
                    if ttl > 0:
                        await self.redis_client.expire(queue_key, ttl)
            
            # Store in history for sender and recipient
            history_keys = [f"message_history:{message.sender_id}"]
            if message.recipient_id:
                history_keys.append(f"message_history:{message.recipient_id}")
            
            for key in history_keys:
                await self.redis_client.lpush(key, message_data)
                await self.redis_client.ltrim(key, 0, 99)  # Keep only last 100 messages
            
        except Exception as e:
            logger.error(f"Error storing message in Redis: {e}")
    
    async def _check_redis_messages(self):
        """Check for pending messages in Redis"""
        try:
            # Check queues for each subscriber
            for subscriber_id in self.subscribers:
                queue_key = f"message_queue:{subscriber_id}"
                
                # Get message without removing from queue
                messages = await self.redis_client.lrange(queue_key, 0, 0)
                
                if messages:
                    # Get the latest message
                    latest_message = messages[0]
                    try:
                        message_dict = json.loads(latest_message)
                        message = Message(**message_dict)
                        
                        # Remove from Redis and deliver locally
                        await self.redis_client.lpop(queue_key)
                        await self._deliver_message(message)
                        
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"Error processing Redis message: {e}")
                        # Remove invalid message
                        await self.redis_client.lpop(queue_key)
                        
        except Exception as e:
            logger.error(f"Error checking Redis messages: {e}")
    
    async def _increment_message_metrics(self):
        """Increment message metrics"""
        try:
            await self.redis_client.incr("metrics:messages_today")
            await self.redis_client.expire("metrics:messages_today", 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error incrementing message metrics: {e}")
    
    def _get_priority_value(self, priority: MessagePriority) -> int:
        """Get numeric priority value"""
        priority_values = {
            MessagePriority.LOW: 1,
            MessagePriority.NORMAL: 2,
            MessagePriority.HIGH: 3,
            MessagePriority.URGENT: 4
        }
        return priority_values.get(priority, 2)
