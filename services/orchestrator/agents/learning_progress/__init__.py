#!/usr/bin/env python3
"""
Jaseci Learning Companion - Learning Progress Agent
Agent for tracking and analyzing learning progress

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from database.connection import get_db

logger = logging.getLogger(__name__)

@dataclass
class LearningProgress:
    """Learning progress data structure"""
    user_id: str
    learning_path_id: str
    lesson_id: str
    progress_percentage: float
    time_spent: int  # seconds
    completed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    session_data: Optional[Dict[str, Any]] = None

class LearningProgressAgent:
    """Enterprise learning progress tracking agent"""
    
    def __init__(self, agent_id: str = "learning_progress_agent"):
        self.agent_id = agent_id
        self.agent_type = "learning_progress"
        self.capabilities = [
            "progress_tracking", 
            "statistics", 
            "milestone_detection",
            "learning_analytics",
            "recommendation_engine"
        ]
        self.status = "initializing"
        self.last_heartbeat = datetime.utcnow()
    
    async def initialize(self):
        """Initialize agent"""
        try:
            self.status = "ready"
            self.last_heartbeat = datetime.utcnow()
            logger.info(f"Learning Progress Agent initialized: {self.agent_id}")
        except Exception as e:
            logger.error(f"Error initializing Learning Progress Agent: {e}")
            self.status = "error"
    
    async def heartbeat(self):
        """Agent heartbeat"""
        self.last_heartbeat = datetime.utcnow()
        self.status = "active"
    
    async def handle_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle learning progress task"""
        try:
            await self.heartbeat()
            
            task_type = task_data.get("task_type")
            
            if task_type == "update_progress":
                return await self._update_progress(task_data)
            elif task_type == "get_statistics":
                return await self._get_statistics(task_data)
            elif task_type == "detect_milestones":
                return await self._detect_milestones(task_data)
            elif task_type == "generate_recommendations":
                return await self._generate_recommendations(task_data)
            elif task_type == "get_learning_path_progress":
                return await self._get_learning_path_progress(task_data)
            else:
                return {"error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"Error handling task in Learning Progress Agent: {e}")
            return {"error": str(e)}
    
    async def _update_progress(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user learning progress"""
        try:
            user_id = task_data.get("user_id")
            learning_path_id = task_data.get("learning_path_id")
            lesson_id = task_data.get("lesson_id")
            progress_data = task_data.get("progress_data", {})
            
            if not all([user_id, learning_path_id, lesson_id]):
                return {"error": "Missing required fields"}
            
            progress = LearningProgress(
                user_id=user_id,
                learning_path_id=learning_path_id,
                lesson_id=lesson_id,
                progress_percentage=progress_data.get("progress_percentage", 0.0),
                time_spent=progress_data.get("time_spent", 0),
                last_activity=datetime.utcnow(),
                session_data=progress_data.get("session_data")
            )
            
            # Store in database
            async with get_db() as conn:
                await conn.execute("""
                    INSERT INTO learning_progress (
                        user_id, learning_path_id, lesson_id, progress_percentage,
                        time_spent, last_activity, session_data, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (user_id, learning_path_id, lesson_id)
                    DO UPDATE SET
                        progress_percentage = EXCLUDED.progress_percentage,
                        time_spent = learning_progress.time_spent + EXCLUDED.time_spent,
                        last_activity = EXCLUDED.last_activity,
                        session_data = EXCLUDED.session_data,
                        updated_at = EXCLUDED.updated_at
                """, progress.user_id, progress.learning_path_id, progress.lesson_id,
                    progress.progress_percentage, progress.time_spent, progress.last_activity,
                    json.dumps(progress.session_data) if progress.session_data else None,
                    datetime.utcnow(), datetime.utcnow())
            
            # Check for milestone achievements
            milestones = await self._check_milestones(user_id, learning_path_id)
            
            # Update learning session
            await self._update_learning_session(user_id, progress)
            
            result = {
                "status": "progress_updated",
                "user_id": user_id,
                "learning_path_id": learning_path_id,
                "lesson_id": lesson_id,
                "progress_percentage": progress.progress_percentage,
                "time_spent": progress.time_spent,
                "milestones": milestones,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Progress updated for user {user_id} in path {learning_path_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return {"error": str(e)}
    
    async def _get_statistics(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get learning statistics"""
        try:
            user_id = task_data.get("user_id")
            learning_path_id = task_data.get("learning_path_id")
            time_period = task_data.get("time_period", "30d")  # 7d, 30d, 90d, all
            
            if not user_id:
                return {"error": "Missing user_id"}
            
            # Calculate date range
            end_date = datetime.utcnow()
            if time_period == "7d":
                start_date = end_date - timedelta(days=7)
            elif time_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif time_period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=365)  # 1 year
            
            async with get_db() as conn:
                # Basic progress statistics
                if learning_path_id:
                    stats_query = """
                        SELECT 
                            COUNT(*) as total_lessons,
                            AVG(progress_percentage) as avg_progress,
                            SUM(time_spent) as total_time_spent,
                            COUNT(CASE WHEN progress_percentage = 100 THEN 1 END) as completed_lessons,
                            MAX(last_activity) as last_activity
                        FROM learning_progress
                        WHERE user_id = $1 AND learning_path_id = $2 
                        AND last_activity BETWEEN $3 AND $4
                    """
                    stats_params = [user_id, learning_path_id, start_date, end_date]
                else:
                    stats_query = """
                        SELECT 
                            COUNT(DISTINCT learning_path_id) as total_paths,
                            COUNT(*) as total_lesson_attempts,
                            AVG(progress_percentage) as avg_progress,
                            SUM(time_spent) as total_time_spent,
                            COUNT(CASE WHEN progress_percentage = 100 THEN 1 END) as completed_lessons,
                            MAX(last_activity) as last_activity
                        FROM learning_progress
                        WHERE user_id = $1 AND last_activity BETWEEN $2 AND $3
                    """
                    stats_params = [user_id, start_date, end_date]
                
                stats = await conn.fetchrow(stats_query, *stats_params)
                
                # Learning streak calculation
                streak_data = await self._calculate_learning_streak(user_id, start_date, end_date)
                
                # Daily activity
                daily_activity = await self._get_daily_activity(user_id, start_date, end_date)
                
                # Learning velocity (lessons per week)
                velocity_data = await self._get_learning_velocity(user_id, start_date, end_date)
                
                result = {
                    "status": "statistics_generated",
                    "user_id": user_id,
                    "time_period": time_period,
                    "statistics": dict(stats) if stats else {},
                    "learning_streak": streak_data,
                    "daily_activity": daily_activity,
                    "learning_velocity": velocity_data,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    async def _detect_milestones(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect learning milestones"""
        try:
            user_id = task_data.get("user_id")
            learning_path_id = task_data.get("learning_path_id")
            
            if not user_id:
                return {"error": "Missing user_id"}
            
            milestones = []
            
            # Get user progress
            async with get_db() as conn:
                if learning_path_id:
                    progress_data = await conn.fetch("""
                        SELECT learning_path_id, lesson_id, progress_percentage, 
                               time_spent, created_at
                        FROM learning_progress
                        WHERE user_id = $1 AND learning_path_id = $2
                        ORDER BY created_at
                    """, user_id, learning_path_id)
                else:
                    progress_data = await conn.fetch("""
                        SELECT learning_path_id, lesson_id, progress_percentage,
                               time_spent, created_at
                        FROM learning_progress
                        WHERE user_id = $1
                        ORDER BY created_at
                    """, user_id)
            
            # Check various milestone conditions
            milestones.extend(await self._check_progress_milestones(progress_data))
            milestones.extend(await self._check_time_milestones(progress_data))
            milestones.extend(await self._check_consistency_milestones(progress_data))
            
            result = {
                "status": "milestones_detected",
                "user_id": user_id,
                "learning_path_id": learning_path_id,
                "milestones": milestones,
                "detected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Detected {len(milestones)} milestones for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error detecting milestones: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate learning recommendations"""
        try:
            user_id = task_data.get("user_id")
            learning_path_id = task_data.get("learning_path_id")
            
            if not user_id:
                return {"error": "Missing user_id"}
            
            recommendations = []
            
            # Get user progress and learning patterns
            async with get_db() as conn:
                # Get current progress
                current_progress = await conn.fetchrow("""
                    SELECT AVG(progress_percentage) as avg_progress,
                           SUM(time_spent) as total_time,
                           COUNT(*) as total_lessons_attempted
                    FROM learning_progress
                    WHERE user_id = $1
                """, user_id)
                
                # Get learning patterns
                learning_patterns = await conn.fetch("""
                    SELECT learning_path_id, AVG(progress_percentage) as path_progress,
                           COUNT(*) as lessons_count
                    FROM learning_progress
                    WHERE user_id = $1
                    GROUP BY learning_path_id
                """, user_id)
            
            # Generate recommendations based on progress
            if current_progress and current_progress["avg_progress"] < 50:
                recommendations.append({
                    "type": "encouragement",
                    "title": "Keep Going!",
                    "message": "You're making good progress. Consider spending more time on challenging concepts.",
                    "priority": "medium"
                })
            
            # Recommendation for time management
            if current_progress and current_progress["total_time"] > 3600:  # More than 1 hour
                recommendations.append({
                    "type": "time_management",
                    "title": "Study Schedule Optimization",
                    "message": "You've been very active! Consider taking breaks and reviewing key concepts.",
                    "priority": "low"
                })
            
            # Recommendations based on learning patterns
            for pattern in learning_patterns:
                if pattern["path_progress"] < 30:
                    recommendations.append({
                        "type": "focus_area",
                        "title": "Focus Area Identified",
                        "message": f"You might want to focus more on learning path {pattern['learning_path_id']}",
                        "priority": "high",
                        "target_path": pattern["learning_path_id"]
                    })
            
            result = {
                "status": "recommendations_generated",
                "user_id": user_id,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"error": str(e)}
    
    async def _get_learning_path_progress(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed learning path progress"""
        try:
            user_id = task_data.get("user_id")
            learning_path_id = task_data.get("learning_path_id")
            
            if not all([user_id, learning_path_id]):
                return {"error": "Missing required fields"}
            
            async with get_db() as conn:
                # Get path progress
                path_progress = await conn.fetchrow("""
                    SELECT lp.*, lp.lesson_title, lp.difficulty_level
                    FROM learning_progress lp
                    WHERE lp.user_id = $1 AND lp.learning_path_id = $2
                    ORDER BY lp.created_at
                """, user_id, learning_path_id)
                
                # Get overall path stats
                path_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_lessons,
                        AVG(progress_percentage) as avg_progress,
                        SUM(time_spent) as total_time_spent,
                        COUNT(CASE WHEN progress_percentage = 100 THEN 1 END) as completed_lessons,
                        MIN(last_activity) as started_at,
                        MAX(last_activity) as last_activity
                    FROM learning_progress
                    WHERE user_id = $1 AND learning_path_id = $2
                """, user_id, learning_path_id)
                
                # Calculate estimated completion time
                remaining_lessons = path_stats["total_lessons"] - path_stats["completed_lessons"]
                avg_time_per_lesson = path_stats["total_time_spent"] / max(path_stats["total_lessons"], 1)
                estimated_remaining_time = remaining_lessons * avg_time_per_lesson
                
                result = {
                    "status": "path_progress_retrieved",
                    "user_id": user_id,
                    "learning_path_id": learning_path_id,
                    "progress": dict(path_progress) if path_progress else {},
                    "statistics": dict(path_stats) if path_stats else {},
                    "estimated_completion_time": estimated_remaining_time,
                    "completion_percentage": (path_stats["completed_lessons"] / max(path_stats["total_lessons"], 1)) * 100
                    if path_stats else 0,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting learning path progress: {e}")
            return {"error": str(e)}
    
    async def _check_milestones(self, user_id: str, learning_path_id: str) -> List[Dict[str, Any]]:
        """Check for milestone achievements"""
        milestones = []
        
        try:
            async with get_db() as conn:
                # Check for progress milestones
                progress_milestones = await conn.fetch("""
                    SELECT learning_path_id, COUNT(*) as completed_lessons
                    FROM learning_progress
                    WHERE user_id = $1 AND learning_path_id = $2 AND progress_percentage = 100
                    GROUP BY learning_path_id
                """, user_id, learning_path_id)
                
                for milestone in progress_milestones:
                    completed_lessons = milestone["completed_lessons"]
                    
                    if completed_lessons == 1:
                        milestones.append({
                            "type": "first_completion",
                            "title": "First Lesson Completed!",
                            "description": "You've completed your first lesson",
                            "achieved_at": datetime.utcnow().isoformat()
                        })
                    elif completed_lessons == 10:
                        milestones.append({
                            "type": "ten_lessons",
                            "title": "Ten Lessons Champion!",
                            "description": "You've completed 10 lessons",
                            "achieved_at": datetime.utcnow().isoformat()
                        })
                    elif completed_lessons == 50:
                        milestones.append({
                            "type": "fifty_lessons",
                            "title": "Learning Master!",
                            "description": "You've completed 50 lessons",
                            "achieved_at": datetime.utcnow().isoformat()
                        })
                
        except Exception as e:
            logger.error(f"Error checking milestones: {e}")
        
        return milestones
    
    async def _update_learning_session(self, user_id: str, progress: LearningProgress):
        """Update learning session tracking"""
        try:
            async with get_db() as conn:
                await conn.execute("""
                    INSERT INTO user_sessions (
                        user_id, session_type, start_time, last_activity,
                        session_data, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (user_id, session_type, start_time::date)
                    DO UPDATE SET
                        last_activity = EXCLUDED.last_activity,
                        session_data = EXCLUDED.session_data,
                        updated_at = EXCLUDED.updated_at
                """, user_id, "learning", progress.last_activity, progress.last_activity,
                    json.dumps(progress.session_data) if progress.session_data else None,
                    datetime.utcnow())
                    
        except Exception as e:
            logger.error(f"Error updating learning session: {e}")
    
    async def _calculate_learning_streak(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate learning streak"""
        try:
            async with get_db() as conn:
                # Get daily activity
                daily_activity = await conn.fetch("""
                    SELECT DATE(last_activity) as activity_date, 
                           COUNT(*) as sessions_count
                    FROM user_sessions
                    WHERE user_id = $1 AND last_activity BETWEEN $2 AND $3
                    GROUP BY DATE(last_activity)
                    ORDER BY activity_date
                """, user_id, start_date, end_date)
                
                # Calculate streak
                current_streak = 0
                longest_streak = 0
                temp_streak = 0
                previous_date = None
                
                for activity in daily_activity:
                    activity_date = activity["activity_date"]
                    
                    if previous_date:
                        days_diff = (activity_date - previous_date).days
                        if days_diff == 1:
                            temp_streak += 1
                        else:
                            longest_streak = max(longest_streak, temp_streak)
                            temp_streak = 1 if days_diff <= 2 else 0
                    else:
                        temp_streak = 1
                    
                    current_streak = temp_streak
                    previous_date = activity_date
                
                longest_streak = max(longest_streak, temp_streak)
                
                return {
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "total_active_days": len(daily_activity)
                }
                
        except Exception as e:
            logger.error(f"Error calculating learning streak: {e}")
            return {"current_streak": 0, "longest_streak": 0, "total_active_days": 0}
    
    async def _get_daily_activity(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily learning activity"""
        try:
            async with get_db() as conn:
                daily_stats = await conn.fetch("""
                    SELECT 
                        DATE(last_activity) as date,
                        COUNT(*) as sessions,
                        SUM(time_spent) as total_time,
                        AVG(progress_percentage) as avg_progress
                    FROM learning_progress lp
                    JOIN user_sessions us ON lp.user_id = us.user_id 
                        AND DATE(lp.last_activity) = DATE(us.last_activity)
                    WHERE lp.user_id = $1 AND lp.last_activity BETWEEN $2 AND $3
                    GROUP BY DATE(lp.last_activity)
                    ORDER BY date
                """, user_id, start_date, end_date)
                
                return [dict(stats) for stats in daily_stats]
                
        except Exception as e:
            logger.error(f"Error getting daily activity: {e}")
            return []
    
    async def _get_learning_velocity(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get learning velocity metrics"""
        try:
            async with get_db() as conn:
                # Get weekly completion rates
                weekly_stats = await conn.fetch("""
                    SELECT 
                        DATE_TRUNC('week', last_activity) as week,
                        COUNT(CASE WHEN progress_percentage = 100 THEN 1 END) as completed_lessons,
                        COUNT(*) as total_attempts,
                        SUM(time_spent) as total_time
                    FROM learning_progress
                    WHERE user_id = $1 AND last_activity BETWEEN $2 AND $3
                    GROUP BY DATE_TRUNC('week', last_activity)
                    ORDER BY week
                """, user_id, start_date, end_date)
                
                if weekly_stats:
                    avg_completions = sum(w["completed_lessons"] for w in weekly_stats) / len(weekly_stats)
                    avg_time = sum(w["total_time"] for w in weekly_stats) / len(weekly_stats)
                else:
                    avg_completions = 0
                    avg_time = 0
                
                return {
                    "weekly_completions_avg": round(avg_completions, 2),
                    "weekly_time_avg": round(avg_time, 2),
                    "velocity_score": round(avg_completions * 10, 2)  # Simple velocity score
                }
                
        except Exception as e:
            logger.error(f"Error getting learning velocity: {e}")
            return {"weekly_completions_avg": 0, "weekly_time_avg": 0, "velocity_score": 0}
    
    async def _check_progress_milestones(self, progress_data: List) -> List[Dict[str, Any]]:
        """Check progress-based milestones"""
        milestones = []
        
        total_completed = sum(1 for p in progress_data if p["progress_percentage"] == 100)
        total_time = sum(p["time_spent"] for p in progress_data)
        
        if total_completed >= 1:
            milestones.append({
                "type": "first_completion",
                "title": "First Lesson Completed",
                "description": "Congratulations on completing your first lesson!",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if total_completed >= 10:
            milestones.append({
                "type": "ten_lessons",
                "title": "10 Lessons Complete",
                "description": "You've completed 10 lessons!",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if total_time >= 3600:  # 1 hour
            milestones.append({
                "type": "one_hour",
                "title": "1 Hour of Learning",
                "description": "You've spent 1 hour learning!",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return milestones
    
    async def _check_time_milestones(self, progress_data: List) -> List[Dict[str, Any]]:
        """Check time-based milestones"""
        milestones = []
        
        # Check for consistent daily activity
        dates = [p["created_at"].date() for p in progress_data]
        unique_dates = sorted(set(dates))
        
        if len(unique_dates) >= 7:
            milestones.append({
                "type": "week_streak",
                "title": "Weekly Learner",
                "description": "You've learned for a full week!",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return milestones
    
    async def _check_consistency_milestones(self, progress_data: List) -> List[Dict[str, Any]]:
        """Check consistency-based milestones"""
        milestones = []
        
        # Check for balanced progress across multiple paths
        path_progress = {}
        for p in progress_data:
            path_id = p.get("learning_path_id", "default")
            if path_id not in path_progress:
                path_progress[path_id] = []
            path_progress[path_id].append(p["progress_percentage"])
        
        # Check if user is making progress in multiple areas
        if len(path_progress) >= 3:
            avg_progress_per_path = [
                sum(path_data) / len(path_data) 
                for path_data in path_progress.values()
            ]
            
            if all(progress > 20 for progress in avg_progress_per_path):
                milestones.append({
                    "type": "well_rounded",
                    "title": "Well-Rounded Learner",
                    "description": "You're making good progress across multiple areas!",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return milestones
