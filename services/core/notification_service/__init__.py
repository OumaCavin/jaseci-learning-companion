#!/usr/bin/env python3
"""
Jaseci Learning Companion - Notification Service
Real-time notification system for user interactions and system events

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from database.connection import get_db, get_redis

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    LEARNING_PROGRESS = "learning_progress"
    QUIZ_COMPLETION = "quiz_completion"
    CODE_ANALYSIS = "code_analysis"
    ACHIEVEMENT = "achievement"
    SYSTEM_ALERT = "system_alert"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    RECOMMENDATION = "recommendation"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryMethod(str, Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

@dataclass
class NotificationData:
    """Notification data structure"""
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    delivery_methods: List[DeliveryMethod] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class NotificationService:
    """Enterprise notification service"""
    
    def __init__(self):
        self.redis_client = None
        self.active_connections: Dict[str, Set[asyncio.Queue]] = {}
        self.email_config = {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("EMAIL_FROM", "Jaseci Learning <noreply@jaseci-learning.com>")
        }
    
    async def initialize(self):
        """Initialize notification service"""
        self.redis_client = get_redis()
        logger.info("Notification service initialized")
    
    async def send_notification(self, notification: NotificationData) -> str:
        """Send notification through specified methods"""
        try:
            # Generate notification ID
            notification_id = await self._generate_notification_id()
            
            # Store notification in database
            await self._store_notification(notification_id, notification)
            
            # Send through each delivery method
            tasks = []
            for method in notification.delivery_methods or [DeliveryMethod.WEBSOCKET]:
                if method == DeliveryMethod.WEBSOCKET:
                    tasks.append(self._send_websocket_notification(notification))
                elif method == DeliveryMethod.EMAIL:
                    tasks.append(self._send_email_notification(notification))
                elif method == DeliveryMethod.PUSH:
                    tasks.append(self._send_push_notification(notification))
            
            # Execute all delivery tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Notification {notification_id} sent to user {notification.user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            raise
    
    async def send_bulk_notification(self, notifications: List[NotificationData]) -> List[str]:
        """Send bulk notifications"""
        try:
            tasks = [self.send_notification(notification) for notification in notifications]
            return await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return []
    
    async def schedule_notification(self, notification: NotificationData) -> str:
        """Schedule notification for later delivery"""
        try:
            notification_id = await self._generate_notification_id()
            
            # Store in database with schedule
            await self._store_scheduled_notification(notification_id, notification)
            
            # Add to Redis scheduler
            schedule_key = f"scheduled_notification:{notification_id}"
            self.redis_client.setex(
                schedule_key,
                int((notification.scheduled_at - datetime.utcnow()).total_seconds()),
                json.dumps({
                    "notification_id": notification_id,
                    "notification_data": {
                        "user_id": notification.user_id,
                        "title": notification.title,
                        "message": notification.message,
                        "notification_type": notification.notification_type.value,
                        "priority": notification.priority.value,
                        "data": notification.data,
                        "delivery_methods": [m.value for m in notification.delivery_methods]
                    }
                })
            )
            
            logger.info(f"Notification {notification_id} scheduled for {notification.scheduled_at}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
            raise
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's notification history"""
        try:
            async with get_db() as conn:
                notifications = await conn.fetch("""
                    SELECT id, title, message, notification_type, priority, 
                           delivery_method, sent_at, read_at, data
                    FROM notifications 
                    WHERE user_id = $1
                    ORDER BY sent_at DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                return [dict(notification) for notification in notifications]
                
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            async with get_db() as conn:
                result = await conn.execute("""
                    UPDATE notifications 
                    SET read_at = $1
                    WHERE id = $2 AND user_id = $3
                """, datetime.utcnow(), notification_id, user_id)
                
                return "UPDATE 1" in result
                
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False
    
    async def mark_all_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        try:
            async with get_db() as conn:
                result = await conn.execute("""
                    UPDATE notifications 
                    SET read_at = $1
                    WHERE user_id = $2 AND read_at IS NULL
                """, datetime.utcnow(), user_id)
                
                # Extract number of updated rows
                updated_count = int(result.split()[-1])
                logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
            return 0
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete notification"""
        try:
            async with get_db() as conn:
                result = await conn.execute("""
                    DELETE FROM notifications 
                    WHERE id = $1 AND user_id = $2
                """, notification_id, user_id)
                
                return "DELETE 1" in result
                
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            return False
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM notifications 
                    WHERE user_id = $1 AND read_at IS NULL
                """, user_id)
                
                return count
                
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}")
            return 0
    
    async def send_learning_milestone(self, user_id: str, milestone_data: Dict[str, Any]) -> str:
        """Send learning milestone notification"""
        notification = NotificationData(
            user_id=user_id,
            title="🎉 Learning Milestone Achieved!",
            message=f"Congratulations! You've {milestone_data['description']}",
            notification_type=NotificationType.LEARNING_PROGRESS,
            priority=NotificationPriority.MEDIUM,
            data=milestone_data,
            delivery_methods=[DeliveryMethod.WEBSOCKET, DeliveryMethod.EMAIL]
        )
        
        return await self.send_notification(notification)
    
    async def send_code_analysis_complete(self, user_id: str, analysis_id: str, analysis_type: str) -> str:
        """Send code analysis completion notification"""
        notification = NotificationData(
            user_id=user_id,
            title="📊 Code Analysis Complete",
            message=f"Your {analysis_type} analysis is ready to view",
            notification_type=NotificationType.CODE_ANALYSIS,
            priority=NotificationPriority.MEDIUM,
            data={"analysis_id": analysis_id, "analysis_type": analysis_type},
            delivery_methods=[DeliveryMethod.WEBSOCKET]
        )
        
        return await self.send_notification(notification)
    
    async def send_achievement_notification(self, user_id: str, achievement_data: Dict[str, Any]) -> str:
        """Send achievement notification"""
        notification = NotificationData(
            user_id=user_id,
            title="🏆 Achievement Unlocked!",
            message=f"You've earned the '{achievement_data['name']}' badge!",
            notification_type=NotificationType.ACHIEVEMENT,
            priority=NotificationPriority.HIGH,
            data=achievement_data,
            delivery_methods=[DeliveryMethod.WEBSOCKET, DeliveryMethod.EMAIL]
        )
        
        return await self.send_notification(notification)
    
    async def send_system_alert(self, user_id: str, alert_data: Dict[str, Any]) -> str:
        """Send system alert notification"""
        notification = NotificationData(
            user_id=user_id,
            title="🔔 System Notification",
            message=alert_data["message"],
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.HIGH,
            data=alert_data,
            delivery_methods=[DeliveryMethod.WEBSOCKET, DeliveryMethod.EMAIL]
        )
        
        return await self.send_notification(notification)
    
    async def send_email_verification(self, user_id: str, email: str, verification_token: str) -> str:
        """Send email verification notification"""
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
        
        notification = NotificationData(
            user_id=user_id,
            title="✉️ Verify Your Email",
            message="Please verify your email address to complete your registration",
            notification_type=NotificationType.EMAIL_VERIFICATION,
            priority=NotificationPriority.HIGH,
            data={"verification_url": verification_url, "email": email},
            delivery_methods=[DeliveryMethod.EMAIL]
        )
        
        return await self.send_notification(notification)
    
    async def send_password_reset(self, user_id: str, email: str, reset_token: str) -> str:
        """Send password reset notification"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        notification = NotificationData(
            user_id=user_id,
            title="🔐 Password Reset Request",
            message="Click the link below to reset your password",
            notification_type=NotificationType.PASSWORD_RESET,
            priority=NotificationPriority.HIGH,
            data={"reset_url": reset_url, "email": email},
            delivery_methods=[DeliveryMethod.EMAIL]
        )
        
        return await self.send_notification(notification)
    
    async def send_recommendation_notification(self, user_id: str, recommendation_data: Dict[str, Any]) -> str:
        """Send learning recommendation notification"""
        notification = NotificationData(
            user_id=user_id,
            title="💡 Personalized Recommendation",
            message=f"Based on your progress, we recommend: {recommendation_data['title']}",
            notification_type=NotificationType.RECOMMENDATION,
            priority=NotificationPriority.LOW,
            data=recommendation_data,
            delivery_methods=[DeliveryMethod.WEBSOCKET]
        )
        
        return await self.send_notification(notification)
    
    async def register_websocket_connection(self, user_id: str, queue: asyncio.Queue):
        """Register WebSocket connection for real-time notifications"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(queue)
        logger.info(f"WebSocket connection registered for user {user_id}")
    
    async def unregister_websocket_connection(self, user_id: str, queue: asyncio.Queue):
        """Unregister WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(queue)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket connection unregistered for user {user_id}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all user's WebSocket connections"""
        if user_id in self.active_connections:
            message_data = json.dumps(message)
            disconnected_connections = set()
            
            for queue in self.active_connections[user_id]:
                try:
                    await queue.put(message_data)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected_connections.add(queue)
            
            # Remove disconnected connections
            for queue in disconnected_connections:
                self.active_connections[user_id].discard(queue)
    
    async def close(self):
        """Close notification service"""
        # Cancel all scheduled notifications
        scheduler_keys = self.redis_client.keys("scheduled_notification:*")
        if scheduler_keys:
            self.redis_client.delete(*scheduler_keys)
        
        logger.info("Notification service closed")
    
    async def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        import uuid
        return f"notif_{timestamp}_{str(uuid.uuid4())[:8]}"
    
    async def _store_notification(self, notification_id: str, notification: NotificationData):
        """Store notification in database"""
        async with get_db() as conn:
            await conn.execute("""
                INSERT INTO notifications (
                    id, user_id, title, message, notification_type, priority,
                    delivery_method, sent_at, data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, notification_id, notification.user_id, notification.title, 
                notification.message, notification.notification_type.value,
                notification.priority.value, 
                ",".join([m.value for m in notification.delivery_methods or []]),
                datetime.utcnow(), notification.data)
    
    async def _store_scheduled_notification(self, notification_id: str, notification: NotificationData):
        """Store scheduled notification in database"""
        async with get_db() as conn:
            await conn.execute("""
                INSERT INTO notifications (
                    id, user_id, title, message, notification_type, priority,
                    delivery_method, scheduled_at, data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, notification_id, notification.user_id, notification.title,
                notification.message, notification.notification_type.value,
                notification.priority.value,
                ",".join([m.value for m in notification.delivery_methods or []]),
                notification.scheduled_at, notification.data)
    
    async def _send_websocket_notification(self, notification: NotificationData):
        """Send WebSocket notification"""
        await self.broadcast_to_user(notification.user_id, {
            "type": "notification",
            "notification": {
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.value,
                "notification_type": notification.notification_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "data": notification.data
            }
        })
    
    async def _send_email_notification(self, notification: NotificationData):
        """Send email notification"""
        try:
            # Get user's email
            async with get_db() as conn:
                user = await conn.fetchrow("""
                    SELECT email, first_name FROM users WHERE id = $1
                """, notification.user_id)
                
                if not user:
                    return
                
                # Send email
                await self._send_email(
                    to_email=user["email"],
                    subject=notification.title,
                    body=self._format_email_body(notification, user["first_name"])
                )
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_push_notification(self, notification: NotificationData):
        """Send push notification (placeholder for mobile/web push)"""
        # This would integrate with a push notification service like Firebase
        logger.info(f"Push notification would be sent for: {notification.title}")
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email via SMTP"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config["from_email"]
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(self.email_config["smtp_host"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            
            text = msg.as_string()
            server.sendmail(self.email_config["from_email"], to_email, text)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
    
    def _format_email_body(self, notification: NotificationData, first_name: str) -> str:
        """Format email body with HTML"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Hello {first_name},</h2>
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1e293b;">{notification.title}</h3>
                    <p>{notification.message}</p>
                    {f'<p><strong>Additional Details:</strong></p><pre>{json.dumps(notification.data, indent=2)}</pre>' if notification.data else ''}
                </div>
                <p style="color: #64748b; font-size: 14px;">
                    This is an automated message from Jaseci Learning Companion.
                    <br>If you have any questions, please contact us at cavin.otieno012@gmail.com
                </p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="color: #64748b; font-size: 12px; text-align: center;">
                    Jaseci Learning Companion<br>
                    Created by Cavin Otieno
                </p>
            </div>
        </body>
        </html>
        """
