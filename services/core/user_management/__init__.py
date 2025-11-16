#!/usr/bin/env python3
"""
Jaseci Learning Companion - User Management Service
Enterprise user lifecycle management service

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from database.connection import get_db

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor" 
    STUDENT = "student"
    USER = "user"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UserManagementService:
    """Enterprise user lifecycle management"""
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with get_db() as conn:
                user = await conn.fetchrow("""
                    SELECT id, email, username, first_name, last_name, role, 
                           is_active, email_verified, created_at, last_login,
                           profile_data, preferences
                    FROM users 
                    WHERE id = $1
                """, user_id)
                
                if user:
                    user_dict = dict(user)
                    # Get additional user stats
                    user_stats = await self._get_user_stats(user_id)
                    user_dict.update(user_stats)
                    return user_dict
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            async with get_db() as conn:
                user = await conn.fetchrow("""
                    SELECT id, email, username, first_name, last_name, role, 
                           is_active, email_verified, created_at, last_login,
                           profile_data, preferences
                    FROM users 
                    WHERE email = $1
                """, email)
                
                return dict(user) if user else None
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            async with get_db() as conn:
                # Update profile data
                await conn.execute("""
                    UPDATE users 
                    SET profile_data = $1, updated_at = $2
                    WHERE id = $3
                """, profile_data, datetime.utcnow(), user_id)
                
                logger.info(f"User profile updated: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Profile update error for {user_id}: {e}")
            return False
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            async with get_db() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET preferences = $1, updated_at = $2
                    WHERE id = $3
                """, preferences, datetime.utcnow(), user_id)
                
                logger.info(f"User preferences updated: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Preferences update error for {user_id}: {e}")
            return False
    
    async def get_users_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get users by role"""
        try:
            async with get_db() as conn:
                users = await conn.fetch("""
                    SELECT id, email, username, first_name, last_name, role, 
                           is_active, email_verified, created_at, last_login
                    FROM users 
                    WHERE role = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """, role.value, limit, offset)
                
                return [dict(user) for user in users]
                
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []
    
    async def search_users(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search users by name, email, or username"""
        try:
            async with get_db() as conn:
                users = await conn.fetch("""
                    SELECT id, email, username, first_name, last_name, role, 
                           is_active, email_verified, created_at
                    FROM users 
                    WHERE (first_name ILIKE $1 OR last_name ILIKE $1 OR 
                           email ILIKE $1 OR username ILIKE $1)
                    AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT $2
                """, f"%{query}%", limit)
                
                return [dict(user) for user in users]
                
        except Exception as e:
            logger.error(f"User search error: {e}")
            return []
    
    async def get_total_users(self) -> int:
        """Get total number of users"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM users WHERE is_active = true
                """)
                return count
                
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0
    
    async def get_active_users_today(self) -> int:
        """Get number of active users today"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM user_sessions 
                    WHERE DATE(last_activity) = CURRENT_DATE
                """)
                return count
                
        except Exception as e:
            logger.error(f"Error getting active users today: {e}")
            return 0
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            async with get_db() as conn:
                # Basic stats
                stats = await self._get_user_stats(user_id)
                
                # Learning progress
                progress_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(lesson_duration) as total_study_time,
                        AVG(lesson_duration) as avg_study_time,
                        COUNT(DISTINCT learning_path_id) as learning_paths_started,
                        COUNT(DISTINCT CASE WHEN completion_percentage = 100 THEN learning_path_id END) as learning_paths_completed
                    FROM learning_progress lp
                    JOIN learning_paths lpr ON lp.learning_path_id = lpr.id
                    WHERE lp.user_id = $1
                """, user_id)
                
                stats.update(dict(progress_stats))
                
                # Code analysis stats
                analysis_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_analyses,
                        COUNT(CASE WHEN analysis_type = 'full' THEN 1 END) as full_analyses,
                        COUNT(CASE WHEN analysis_type = 'osp' THEN 1 END) as osp_analyses,
                        AVG(analysis_duration) as avg_analysis_time
                    FROM code_analysis ca
                    WHERE ca.user_id = $1
                """, user_id)
                
                stats.update(dict(analysis_stats))
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting user statistics for {user_id}: {e}")
            return {}
    
    async def create_learning_session(self, user_id: str, session_data: Dict[str, Any]) -> Optional[str]:
        """Create learning session tracking"""
        try:
            async with get_db() as conn:
                session_id = await conn.fetchval("""
                    INSERT INTO user_sessions (
                        user_id, session_type, start_time, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, user_id, session_data.get("type"), datetime.utcnow(), 
                    session_data.get("metadata", {}), datetime.utcnow())
                
                logger.info(f"Learning session created: {session_id}")
                return str(session_id)
                
        except Exception as e:
            logger.error(f"Error creating learning session for {user_id}: {e}")
            return None
    
    async def update_learning_session(self, session_id: str, activity_data: Dict[str, Any]) -> bool:
        """Update learning session activity"""
        try:
            async with get_db() as conn:
                await conn.execute("""
                    UPDATE user_sessions 
                    SET last_activity = $1, activity_data = $2, updated_at = $3
                    WHERE id = $4
                """, datetime.utcnow(), activity_data, datetime.utcnow(), session_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating learning session {session_id}: {e}")
            return False
    
    async def end_learning_session(self, session_id: str, end_data: Dict[str, Any]) -> bool:
        """End learning session"""
        try:
            async with get_db() as conn:
                await conn.execute("""
                    UPDATE user_sessions 
                    SET end_time = $1, total_duration = EXTRACT(EPOCH FROM ($1 - start_time)), 
                        end_data = $2, updated_at = $3
                    WHERE id = $4
                """, datetime.utcnow(), end_data, datetime.utcnow(), session_id)
                
                logger.info(f"Learning session ended: {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error ending learning session {session_id}: {e}")
            return False
    
    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user achievements and badges"""
        try:
            async with get_db() as conn:
                achievements = await conn.fetch("""
                    SELECT a.id, a.name, a.description, a.badge_icon, a.criteria,
                           ua.earned_at, ua.progress
                    FROM achievements a
                    JOIN user_achievements ua ON a.id = ua.achievement_id
                    WHERE ua.user_id = $1
                    ORDER BY ua.earned_at DESC
                """, user_id)
                
                return [dict(achievement) for achievement in achievements]
                
        except Exception as e:
            logger.error(f"Error getting user achievements for {user_id}: {e}")
            return []
    
    async def award_achievement(self, user_id: str, achievement_id: str, progress: Dict[str, Any] = None) -> bool:
        """Award achievement to user"""
        try:
            async with get_db() as conn:
                # Check if user already has this achievement
                existing = await conn.fetchval("""
                    SELECT id FROM user_achievements 
                    WHERE user_id = $1 AND achievement_id = $2
                """, user_id, achievement_id)
                
                if existing:
                    # Update progress if exists
                    await conn.execute("""
                        UPDATE user_achievements 
                        SET progress = $1, updated_at = $2
                        WHERE user_id = $3 AND achievement_id = $4
                    """, progress, datetime.utcnow(), user_id, achievement_id)
                else:
                    # Award new achievement
                    await conn.execute("""
                        INSERT INTO user_achievements (
                            user_id, achievement_id, earned_at, progress, created_at
                        ) VALUES ($1, $2, $3, $4, $5)
                    """, user_id, achievement_id, datetime.utcnow(), progress, datetime.utcnow())
                    
                    logger.info(f"Achievement {achievement_id} awarded to user {user_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error awarding achievement {achievement_id} to user {user_id}: {e}")
            return False
    
    async def get_user_learning_streak(self, user_id: str) -> Dict[str, int]:
        """Get user's learning streak information"""
        try:
            async with get_db() as conn:
                # Get current streak
                current_streak = await conn.fetchval("""
                    SELECT COUNT(DISTINCT DATE(last_activity)) 
                    FROM user_sessions 
                    WHERE user_id = $1 
                    AND last_activity >= CURRENT_DATE - INTERVAL '30 days'
                    AND last_activity >= (
                        SELECT MAX(last_activity) FROM user_sessions 
                        WHERE user_id = $1 AND last_activity < CURRENT_DATE
                    )
                    ORDER BY last_activity DESC
                """, user_id)
                
                # Get longest streak
                longest_streak = await conn.fetchval("""
                    SELECT MAX(streak_length) FROM (
                        SELECT 
                            COUNT(DISTINCT DATE(last_activity)) as streak_length
                        FROM user_sessions 
                        WHERE user_id = $1 
                        AND last_activity >= CURRENT_DATE - INTERVAL '365 days'
                        GROUP BY DATE(last_activity)
                    ) streaks
                """, user_id)
                
                return {
                    "current_streak": current_streak or 0,
                    "longest_streak": longest_streak or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting learning streak for user {user_id}: {e}")
            return {"current_streak": 0, "longest_streak": 0}
    
    async def close(self):
        """Close database connections"""
        logger.info("User management service closed")
    
    async def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get basic user statistics"""
        try:
            async with get_db() as conn:
                # Get various counts
                learning_sessions = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_sessions WHERE user_id = $1
                """, user_id)
                
                code_analyses = await conn.fetchval("""
                    SELECT COUNT(*) FROM code_analysis WHERE user_id = $1
                """, user_id)
                
                quizzes_taken = await conn.fetchval("""
                    SELECT COUNT(*) FROM quiz_attempts WHERE user_id = $1
                """, user_id)
                
                last_activity = await conn.fetchval("""
                    SELECT last_activity FROM user_sessions 
                    WHERE user_id = $1 
                    ORDER BY last_activity DESC 
                    LIMIT 1
                """, user_id)
                
                return {
                    "learning_sessions_count": learning_sessions,
                    "code_analyses_count": code_analyses,
                    "quizzes_taken_count": quizzes_taken,
                    "last_activity": last_activity.isoformat() if last_activity else None
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {
                "learning_sessions_count": 0,
                "code_analyses_count": 0,
                "quizzes_taken_count": 0,
                "last_activity": None
            }
    
    async def get_total_analyses(self) -> int:
        """Get total number of code analyses"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM code_analysis
                """)
                return count
                
        except Exception as e:
            logger.error(f"Error getting total analyses: {e}")
            return 0
    
    async def get_osp_graphs_count(self) -> int:
        """Get total number of OSP graphs created"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(DISTINCT project_id) FROM osp_graphs
                """)
                return count
                
        except Exception as e:
            logger.error(f"Error getting OSP graphs count: {e}")
            return 0
