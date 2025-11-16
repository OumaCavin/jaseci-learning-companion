"""
Learning Progress Agent
Real-time progress tracking and analytics for the Jaseci Learning Companion

This agent tracks user learning progress, analyzes learning patterns, 
provides insights, and updates learning metrics in real-time.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import statistics
from collections import defaultdict, deque

import asyncpg
import redis.asyncio as redis
import nats
from pydantic import BaseModel, Field, validator

from ..registry import Agent, AgentMetadata, AgentType, AgentStatus, Priority, AgentTask


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models for Learning Progress
class LearningSession(BaseModel):
    """Learning session model"""
    session_id: UUID
    user_id: UUID
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    activities_completed: List[str] = []
    code_submissions: int = 0
    quiz_attempts: int = 0
    exercises_completed: int = 0
    average_session_score: float = 0.0
    engagement_level: str = "medium"  # low, medium, high
    learning_velocity: float = 0.0  # concepts per minute


class ProgressUpdate(BaseModel):
    """Real-time progress update"""
    user_id: UUID
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    exercise_id: Optional[UUID] = None
    progress_type: str  # lesson_start, lesson_complete, exercise_attempt, code_submission, quiz_complete
    progress_percentage: float = Field(ge=0, le=100)
    time_spent_minutes: int = 0
    status: str = "in_progress"
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LearningAnalytics(BaseModel):
    """Learning analytics and insights"""
    user_id: UUID
    analytics_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).date())
    
    # Daily metrics
    sessions_count: int = 0
    total_time_minutes: int = 0
    lessons_accessed: int = 0
    lessons_completed: int = 0
    exercises_attempted: int = 0
    exercises_passed: int = 0
    code_submissions: int = 0
    average_score: float = 0.0
    
    # Learning patterns
    peak_learning_hours: List[int] = Field(default_factory=list)
    preferred_session_length: float = 0.0
    learning_streak_days: int = 0
    engagement_trend: str = "stable"  # increasing, stable, decreasing
    
    # Performance metrics
    mastery_velocity: float = 0.0  # concepts mastered per day
    retention_rate: float = 0.0  # percentage of concepts remembered
    problem_solving_speed: float = 0.0  # average time per exercise
    
    # Recommendations
    next_lesson_recommendation: Optional[str] = None
    suggested_session_length: int = 30
    focus_areas: List[str] = Field(default_factory=list)
    difficulty_adjustment: str = "maintain"  # increase, maintain, decrease


class UserProgressProfile(BaseModel):
    """Comprehensive user progress profile"""
    user_id: UUID
    profile_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Overall progress
    total_courses_enrolled: int = 0
    total_lessons_completed: int = 0
    total_exercises_passed: int = 0
    overall_progress_percentage: float = 0.0
    
    # Learning style analysis
    preferred_learning_pace: str = "moderate"  # slow, moderate, fast
    peak_performance_hours: List[int] = Field(default_factory=list)
    preferred_content_types: List[str] = Field(default_factory=list)
    difficulty_preference: str = "challenging"  # easy, challenging, adaptive
    
    # Engagement metrics
    current_streak_days: int = 0
    longest_streak_days: int = 0
    average_daily_time: float = 0.0
    engagement_score: float = 0.0  # 0-100
    
    # Performance characteristics
    learning_velocity_trend: str = "improving"  # improving, stable, declining
    success_rate: float = 0.0  # percentage of successful attempts
    average_quality_score: float = 0.0
    
    # Mastery tracking
    mastered_concepts: List[str] = Field(default_factory=list)
    struggling_concepts: List[str] = Field(default_factory=list)
    review_needed_concepts: List[str] = Field(default_factory=list)


class LearningProgressAgent(Agent):
    """Learning Progress Tracking Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id=uuid4(),
            agent_type=AgentType.LEARNING_PROGRESS,
            name="Learning Progress Tracker",
            version="2.0.0-enterprise"
        )
        self.redis_client = None
        self.database_pool = None
        self.nats_client = None
        self.active_sessions: Dict[str, LearningSession] = {}
        self.progress_buffer: deque = deque(maxlen=1000)
        
    async def initialize(self) -> bool:
        """Initialize the Learning Progress Agent"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url("redis://localhost:6379")
            await self.redis_client.ping()
            
            # Initialize database connection pool
            self.database_pool = await asyncpg.create_pool(
                "postgresql://user:password@localhost/jaseci_learning",
                min_size=5,
                max_size=20
            )
            
            # Initialize NATS connection
            self.nats_client = await nats.connect("nats://localhost:4222")
            
            # Register agent capabilities
            await self.register_capability("track_learning_progress")
            await self.register_capability("analyze_learning_patterns")
            await self.register_capability("generate_insights")
            await self.register_capability("update_analytics")
            await self.register_capability("calculate_engagement_metrics")
            await self.register_capability("detect_learning_trends")
            
            # Subscribe to NATS subjects
            await self.nats_client.subscribe("progress.updates.*", self._handle_progress_update)
            await self.nats_client.subscribe("analytics.events.*", self._handle_analytics_event)
            await self.nats_client.subscribe("session.events.*", self._handle_session_event)
            
            logger.info("Learning Progress Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Learning Progress Agent: {e}")
            return False
            
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process learning progress tasks"""
        try:
            task_type = task.task_type
            
            if task_type == "update_progress":
                return await self._update_progress(task.payload)
            elif task_type == "analyze_patterns":
                return await self._analyze_learning_patterns(task.payload)
            elif task_type == "generate_insights":
                return await self._generate_learning_insights(task.payload)
            elif task_type == "calculate_engagement":
                return await self._calculate_engagement_metrics(task.payload)
            elif task_type == "get_user_profile":
                return await self._get_user_progress_profile(task.payload)
            elif task_type == "update_session":
                return await self._update_learning_session(task.payload)
            elif task_type == "get_analytics":
                return await self._get_learning_analytics(task.payload)
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            return {"status": "error", "message": str(e)}
            
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            health_status = {
                "agent_status": "healthy",
                "active_sessions": len(self.active_sessions),
                "progress_buffer_size": len(self.progress_buffer),
                "redis_connected": False,
                "database_connected": False,
                "nats_connected": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
                health_status["redis_connected"] = True
                
            # Check database
            if self.database_pool:
                async with self.database_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["database_connected"] = True
                
            # Check NATS
            if self.nats_client:
                health_status["nats_connected"] = self.nats_client.is_connected
                
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "agent_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    async def _handle_progress_update(self, msg):
        """Handle progress update events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._update_progress(data)
        except Exception as e:
            logger.error(f"Error handling progress update: {e}")
            
    async def _handle_analytics_event(self, msg):
        """Handle analytics events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._process_analytics_event(data)
        except Exception as e:
            logger.error(f"Error handling analytics event: {e}")
            
    async def _handle_session_event(self, msg):
        """Handle session events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._update_learning_session(data)
        except Exception as e:
            logger.error(f"Error handling session event: {e}")
            
    async def _update_progress(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update user learning progress"""
        try:
            progress_update = ProgressUpdate(**payload)
            
            # Store in Redis for quick access
            progress_key = f"progress:{progress_update.user_id}:{progress_update.lesson_id}"
            await self.redis_client.hset(
                progress_key,
                {
                    "progress_percentage": progress_update.progress_percentage,
                    "status": progress_update.status,
                    "last_updated": progress_update.timestamp.isoformat(),
                    "time_spent": progress_update.time_spent_minutes
                }
            )
            
            # Store in database for persistence
            async with self.database_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO lesson_progress (
                        user_id, lesson_id, status, progress_percentage,
                        time_spent_minutes, last_accessed
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (user_id, lesson_id)
                    DO UPDATE SET
                        status = $3,
                        progress_percentage = $4,
                        time_spent_minutes = $5,
                        last_accessed = $6
                """, 
                    progress_update.user_id,
                    progress_update.lesson_id,
                    progress_update.status,
                    progress_update.progress_percentage,
                    progress_update.time_spent_minutes,
                    progress_update.timestamp
                )
            
            # Update real-time analytics
            await self._update_real_time_analytics(progress_update)
            
            # Emit progress update via WebSocket
            await self._emit_progress_update(progress_update)
            
            logger.info(f"Updated progress for user {progress_update.user_id}: {progress_update.progress_percentage}%")
            
            return {
                "status": "success",
                "message": "Progress updated successfully",
                "progress_percentage": progress_update.progress_percentage
            }
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _analyze_learning_patterns(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user learning patterns"""
        try:
            user_id = payload.get("user_id")
            days_back = payload.get("days_back", 30)
            
            # Get learning data for analysis
            async with self.database_pool.acquire() as conn:
                # Get session data
                sessions = await conn.fetch("""
                    SELECT * FROM learning_summaries 
                    WHERE user_id = $1 AND summary_date >= $2
                    ORDER BY summary_date DESC
                """, user_id, datetime.now(timezone.utc).date() - timedelta(days=days_back))
                
                # Get progress data
                progress_data = await conn.fetch("""
                    SELECT * FROM lesson_progress 
                    WHERE user_id = $1
                    ORDER BY last_accessed DESC
                """, user_id)
            
            # Analyze patterns
            analytics = await self._calculate_learning_analytics(sessions, progress_data)
            
            # Store analytics
            await self._store_learning_analytics(user_id, analytics)
            
            return {
                "status": "success",
                "analytics": analytics,
                "analysis_period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _generate_learning_insights(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning insights"""
        try:
            user_id = payload.get("user_id")
            
            # Get user profile
            profile = await self._get_user_progress_profile({"user_id": user_id})
            
            # Get recent analytics
            analytics = await self._get_learning_analytics({"user_id": user_id})
            
            # Generate insights
            insights = await self._generate_personalized_insights(profile, analytics)
            
            return {
                "status": "success",
                "insights": insights,
                "user_id": user_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _calculate_engagement_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate user engagement metrics"""
        try:
            user_id = payload.get("user_id")
            
            async with self.database_pool.acquire() as conn:
                # Get recent activity data
                activities = await conn.fetch("""
                    SELECT * FROM analytics_events 
                    WHERE user_id = $1 AND event_timestamp >= $2
                    ORDER BY event_timestamp DESC
                """, user_id, datetime.now(timezone.utc) - timedelta(days=7))
                
                # Calculate engagement metrics
                metrics = await self._calculate_engagement_metrics_from_data(activities)
                
            return {
                "status": "success",
                "engagement_metrics": metrics,
                "user_id": user_id,
                "calculation_date": datetime.now(timezone.utc).date().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_user_progress_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive user progress profile"""
        try:
            user_id = payload.get("user_id")
            
            async with self.database_pool.acquire() as conn:
                # Get enrollment data
                enrollments = await conn.fetch("""
                    SELECT * FROM enrollments WHERE user_id = $1
                """, user_id)
                
                # Get lesson progress
                lesson_progress = await conn.fetch("""
                    SELECT * FROM lesson_progress WHERE user_id = $1
                """, user_id)
                
                # Get exercise submissions
                submissions = await conn.fetch("""
                    SELECT * FROM exercise_submissions WHERE user_id = $1
                """, user_id)
                
                # Get quality assessments
                assessments = await conn.fetch("""
                    SELECT * FROM quality_assessments qa
                    JOIN exercise_submissions es ON qa.submission_id = es.submission_id
                    WHERE es.user_id = $1
                """, user_id)
            
            # Build comprehensive profile
            profile = await self._build_user_progress_profile(
                user_id, enrollments, lesson_progress, submissions, assessments
            )
            
            return {
                "status": "success",
                "profile": profile.dict(),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _update_learning_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning session data"""
        try:
            session_data = LearningSession(**payload)
            
            # Update or create session
            self.active_sessions[str(session_data.session_id)] = session_data
            
            # Store in database
            async with self.database_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO learning_sessions (
                        session_id, user_id, course_id, lesson_id, start_time,
                        duration_minutes, activities_completed, code_submissions,
                        quiz_attempts, exercises_completed
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (session_id) DO UPDATE SET
                        duration_minutes = $6,
                        activities_completed = $7,
                        code_submissions = $8,
                        quiz_attempts = $9,
                        exercises_completed = $10
                """,
                    session_data.session_id,
                    session_data.user_id,
                    session_data.course_id,
                    session_data.lesson_id,
                    session_data.start_time,
                    session_data.duration_minutes,
                    json.dumps(session_data.activities_completed),
                    session_data.code_submissions,
                    session_data.quiz_attempts,
                    session_data.exercises_completed
                )
            
            # Update session analytics
            await self._update_session_analytics(session_data)
            
            return {
                "status": "success",
                "session_id": str(session_data.session_id),
                "message": "Session updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_learning_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get learning analytics for user"""
        try:
            user_id = payload.get("user_id")
            days_back = payload.get("days_back", 30)
            
            async with self.database_pool.acquire() as conn:
                analytics_data = await conn.fetch("""
                    SELECT * FROM learning_summaries 
                    WHERE user_id = $1 AND summary_date >= $2
                    ORDER BY summary_date DESC
                """, user_id, datetime.now(timezone.utc).date() - timedelta(days=days_back))
                
                # Calculate summary statistics
                if analytics_data:
                    total_time = sum(record['total_time_minutes'] for record in analytics_data)
                    avg_score = statistics.mean(record['average_quality_score'] for record in analytics_data)
                    total_sessions = sum(record['sessions_count'] for record in analytics_data)
                    
                    summary = {
                        "period_days": days_back,
                        "total_time_minutes": total_time,
                        "average_daily_time": total_time / len(analytics_data),
                        "total_sessions": total_sessions,
                        "average_score": avg_score,
                        "daily_breakdown": [
                            {
                                "date": record['summary_date'].isoformat(),
                                "time_minutes": record['total_time_minutes'],
                                "score": record['average_quality_score'],
                                "sessions": record['sessions_count']
                            }
                            for record in analytics_data
                        ]
                    }
                else:
                    summary = {
                        "period_days": days_back,
                        "total_time_minutes": 0,
                        "average_daily_time": 0,
                        "total_sessions": 0,
                        "average_score": 0,
                        "daily_breakdown": []
                    }
            
            return {
                "status": "success",
                "analytics": summary,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"status": "error", "message": str(e)}
            
    # Helper methods
    async def _update_real_time_analytics(self, progress_update: ProgressUpdate):
        """Update real-time analytics for progress updates"""
        # This would implement real-time analytics calculation
        pass
        
    async def _emit_progress_update(self, progress_update: ProgressUpdate):
        """Emit progress update via message bus"""
        if self.nats_client:
            message = {
                "user_id": str(progress_update.user_id),
                "progress_percentage": progress_update.progress_percentage,
                "status": progress_update.status,
                "timestamp": progress_update.timestamp.isoformat()
            }
            await self.nats_client.publish(
                f"progress.updates.{progress_update.user_id}",
                json.dumps(message).encode()
            )
            
    async def _calculate_learning_analytics(self, sessions: List, progress_data: List) -> LearningAnalytics:
        """Calculate learning analytics from raw data"""
        # Implementation of analytics calculation
        analytics = LearningAnalytics(
            user_id=sessions[0]['user_id'] if sessions else UUID('00000000-0000-0000-0000-000000000000')
        )
        
        # Calculate metrics from sessions
        if sessions:
            analytics.sessions_count = len(sessions)
            analytics.total_time_minutes = sum(record['total_time_minutes'] for record in sessions)
            analytics.average_score = statistics.mean(
                record['average_quality_score'] for record in sessions if record['average_quality_score']
            ) if any(record['average_quality_score'] for record in sessions) else 0.0
            
        return analytics
        
    async def _store_learning_analytics(self, user_id: UUID, analytics: LearningAnalytics):
        """Store learning analytics in database"""
        async with self.database_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO learning_summaries (
                    user_id, summary_date, total_time_minutes, average_quality_score
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, summary_date) DO UPDATE SET
                    total_time_minutes = $3,
                    average_quality_score = $4
            """, 
                user_id, 
                analytics.analytics_date, 
                analytics.total_time_minutes, 
                analytics.average_score
            )
            
    async def _generate_personalized_insights(self, profile: Dict, analytics: Dict) -> List[str]:
        """Generate personalized learning insights"""
        insights = []
        
        # Analyze learning patterns
        if profile.get('current_streak_days', 0) > 7:
            insights.append("Great job maintaining your learning streak! Keep it up!")
            
        avg_daily_time = analytics.get('average_daily_time', 0)
        if avg_daily_time > 60:
            insights.append("You're spending significant time learning - consider taking regular breaks")
        elif avg_daily_time < 15:
            insights.append("Try to dedicate more time daily for better learning outcomes")
            
        return insights
        
    async def _calculate_engagement_metrics_from_data(self, activities: List) -> Dict[str, Any]:
        """Calculate engagement metrics from activity data"""
        # Implementation of engagement calculation
        return {
            "engagement_score": 75.0,  # Placeholder
            "activity_frequency": "high",
            "preferred_times": [9, 14, 20],
            "session_length_preference": 45
        }
        
    async def _build_user_progress_profile(self, user_id: UUID, enrollments: List, 
                                          lesson_progress: List, submissions: List, 
                                          assessments: List) -> UserProgressProfile:
        """Build comprehensive user progress profile"""
        total_completed = len([p for p in lesson_progress if p['status'] == 'completed'])
        total_passed = len([s for s in submissions if s['status'] == 'passed'])
        
        # Calculate average quality score
        avg_quality = statistics.mean(
            record['overall_score'] for record in assessments if record['overall_score']
        ) if assessments else 0.0
        
        profile = UserProgressProfile(
            user_id=user_id,
            total_courses_enrolled=len(enrollments),
            total_lessons_completed=total_completed,
            total_exercises_passed=total_passed,
            overall_progress_percentage=(total_completed / max(len(lesson_progress), 1)) * 100,
            average_quality_score=avg_quality,
            success_rate=(total_passed / max(len(submissions), 1)) * 100 if submissions else 0.0
        )
        
        return profile
        
    async def _update_session_analytics(self, session: LearningSession):
        """Update session analytics"""
        # Implementation for session analytics
        pass
        
    async def _process_analytics_event(self, event_data: Dict[str, Any]):
        """Process analytics events"""
        # Implementation for event processing
        pass


# Agent factory function
def create_learning_progress_agent() -> LearningProgressAgent:
    """Create and configure Learning Progress Agent"""
    return LearningProgressAgent()


# Export
__all__ = [
    "LearningProgressAgent",
    "LearningSession", 
    "ProgressUpdate",
    "LearningAnalytics",
    "UserProgressProfile",
    "create_learning_progress_agent"
]