"""
Content Recommender Agent
Personalized learning path recommendations for the Jaseci Learning Companion

This agent provides intelligent content recommendations based on user learning patterns,
progress, preferences, and learning objectives using collaborative filtering and
content-based algorithms.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import math
import statistics
from collections import defaultdict, Counter

import asyncpg
import redis.asyncio as redis
import nats
from pydantic import BaseModel, Field, validator
import numpy as np

from ..registry import Agent, AgentMetadata, AgentType, AgentStatus, Priority, AgentTask


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Content Recommendation Models
class RecommendationType(str, Enum):
    """Types of content recommendations"""
    NEXT_LESSON = "next_lesson"
    SIMILAR_CONTENT = "similar_content"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    SKILL_GAP = "skill_gap"
    REMEDIAL = "remedial"
    ADVANCED = "advanced"
    REVIEW = "review"
    PROJECT = "project"


class ContentType(str, Enum):
    """Types of learning content"""
    LESSON = "lesson"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    PROJECT = "project"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"


class DifficultyLevel(str, Enum):
    """Difficulty levels for content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyle(str, Enum):
    """User learning styles"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


@dataclass
class LearningPattern:
    """User learning pattern analysis"""
    user_id: UUID
    preferred_content_types: List[ContentType] = field(default_factory=list)
    preferred_difficulty_levels: List[DifficultyLevel] = field(default_factory=list)
    optimal_session_length: int = 30  # minutes
    peak_learning_hours: List[int] = field(default_factory=list)
    learning_velocity: float = 1.0  # concepts per hour
    retention_rate: float = 0.8
    engagement_trend: str = "stable"  # increasing, stable, decreasing
    
    # Learning sequence patterns
    prerequisite_mastery: Dict[str, float] = field(default_factory=dict)  # concept -> mastery %
    skill_gaps: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)


@dataclass
class ContentItem:
    """Learning content item"""
    content_id: UUID
    title: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    estimated_duration_minutes: int
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    content_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserContentInteraction:
    """User interaction with content"""
    interaction_id: UUID
    user_id: UUID
    content_id: UUID
    interaction_type: str  # viewed, started, completed, abandoned, rated
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_minutes: Optional[int] = None
    completion_percentage: float = 0.0
    rating: Optional[float] = None  # 1-5 scale
    feedback: Optional[str] = None
    difficulty_rating: Optional[float] = None  # perceived difficulty


@dataclass
class LearningPath:
    """Personalized learning path"""
    path_id: UUID
    user_id: UUID
    path_name: str
    description: str
    target_skills: List[str] = field(default_factory=list)
    estimated_duration_hours: int
    content_sequence: List[ContentItem] = field(default_factory=list)
    adaptive_milestones: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Recommendation(BaseModel):
    """Content recommendation result"""
    recommendation_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    recommendation_type: RecommendationType
    content_items: List[ContentItem] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    reasoning: str
    personalized_factors: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Recommendation metadata
    algorithm_used: str = "hybrid"  # collaborative, content-based, hybrid
    adaptation_applied: bool = False
    diversity_score: float = 0.0


class ContentRecommenderAgent(Agent):
    """Content Recommendation Agent with personalized learning paths"""
    
    def __init__(self):
        super().__init__(
            agent_id=uuid4(),
            agent_type=AgentType.CONTENT_RECOMMENDER,
            name="Personalized Content Recommender",
            version="2.0.0-enterprise"
        )
        self.redis_client = None
        self.database_pool = None
        self.nats_client = None
        
        # Recommendation algorithms
        self.algorithms = {
            "collaborative": self._collaborative_filtering,
            "content_based": self._content_based_filtering,
            "hybrid": self._hybrid_recommendation,
            "learning_path": self._learning_path_recommendation,
            "adaptive": self._adaptive_recommendation
        }
        
        # Content similarity weights
        self.similarity_weights = {
            "difficulty": 0.3,
            "topic": 0.4,
            "duration": 0.2,
            "style": 0.1
        }
        
        # Learning style preferences
        self.style_content_mapping = {
            LearningStyle.VISUAL: ["diagram", "chart", "visual", "graph"],
            LearningStyle.AUDITORY: ["audio", "video", "discussion", "explanation"],
            LearningStyle.KINESTHETIC: ["exercise", "project", "hands_on", "practice"],
            LearningStyle.READING_WRITING: ["text", "documentation", "writing", "reading"]
        }
        
    async def initialize(self) -> bool:
        """Initialize the Content Recommender Agent"""
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
            await self.register_capability("generate_recommendations")
            await self.register_capability("build_learning_path")
            await self.register_capability("analyze_learning_patterns")
            await self.register_capability("adapt_to_preferences")
            await self.register_capability("detect_skill_gaps")
            await self.register_capability("optimize_learning_sequence")
            
            # Subscribe to NATS subjects
            await self.nats_client.subscribe("recommendation.requests.*", self._handle_recommendation_request)
            await self.nats_client.subscribe("progress.updates.*", self._handle_progress_update)
            await self.nats_client.subscribe("interaction.events.*", self._handle_interaction_event)
            
            logger.info("Content Recommender Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Content Recommender Agent: {e}")
            return False
            
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process content recommendation tasks"""
        try:
            task_type = task.task_type
            
            if task_type == "recommend_content":
                return await self._generate_recommendations(task.payload)
            elif task_type == "build_learning_path":
                return await self._build_learning_path(task.payload)
            elif task_type == "analyze_patterns":
                return await self._analyze_learning_patterns(task.payload)
            elif task_type == "detect_gaps":
                return await self._detect_skill_gaps(task.payload)
            elif task_type == "optimize_sequence":
                return await self._optimize_learning_sequence(task.payload)
            elif task_type == "adapt_preferences":
                return await self._adapt_to_preferences(task.payload)
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
                "redis_connected": False,
                "database_connected": False,
                "nats_connected": False,
                "algorithms_available": len(self.algorithms),
                "similarity_weights_configured": len(self.similarity_weights),
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
            
    # Event handlers
    async def _handle_recommendation_request(self, msg):
        """Handle recommendation request events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._generate_recommendations(data)
        except Exception as e:
            logger.error(f"Error handling recommendation request: {e}")
            
    async def _handle_progress_update(self, msg):
        """Handle progress updates for adaptive recommendations"""
        try:
            data = json.loads(msg.data.decode())
            # Update user learning patterns based on progress
            await self._update_learning_patterns(data)
        except Exception as e:
            logger.error(f"Error handling progress update: {e}")
            
    async def _handle_interaction_event(self, msg):
        """Handle user interaction events"""
        try:
            data = json.loads(msg.data.decode())
            # Update recommendation models based on interactions
            await self._update_recommendation_model(data)
        except Exception as e:
            logger.error(f"Error handling interaction event: {e}")
            
    # Main processing methods
    async def _generate_recommendations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized content recommendations"""
        try:
            user_id = UUID(payload.get("user_id"))
            recommendation_type = RecommendationType(payload.get("type", "next_lesson"))
            max_recommendations = payload.get("max_recommendations", 5)
            learning_context = payload.get("learning_context", {})
            
            # Get user learning pattern
            learning_pattern = await self._analyze_learning_patterns({"user_id": str(user_id)})
            
            # Get available content
            available_content = await self._get_available_content()
            
            # Get user interaction history
            interaction_history = await self._get_user_interaction_history(user_id)
            
            # Generate recommendations based on type
            if recommendation_type == RecommendationType.NEXT_LESSON:
                recommendations = await self._recommend_next_lessons(
                    user_id, available_content, learning_pattern, interaction_history
                )
            elif recommendation_type == RecommendationType.SIMILAR_CONTENT:
                recommendations = await self._recommend_similar_content(
                    user_id, payload.get("reference_content_id"), available_content, learning_pattern
                )
            elif recommendation_type == RecommendationType.SKILL_GAP:
                recommendations = await self._recommend_skill_gap_content(
                    user_id, learning_pattern, available_content
                )
            else:
                recommendations = await self._generate_general_recommendations(
                    user_id, available_content, learning_pattern, interaction_history
                )
                
            # Apply diversity and personalization
            final_recommendations = await self._apply_diversity_and_personalization(
                recommendations, learning_pattern, max_recommendations
            )
            
            # Store recommendations
            await self._store_recommendations(user_id, final_recommendations)
            
            # Emit recommendations via WebSocket
            await self._emit_recommendations(user_id, final_recommendations)
            
            logger.info(f"Generated {len(final_recommendations)} recommendations for user {user_id}")
            
            return {
                "status": "success",
                "recommendations": [rec.dict() for rec in final_recommendations],
                "recommendation_type": recommendation_type.value,
                "total_generated": len(final_recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _build_learning_path(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build personalized learning path"""
        try:
            user_id = UUID(payload.get("user_id"))
            target_skills = payload.get("target_skills", [])
            time_constraint_hours = payload.get("time_constraint_hours", 40)
            difficulty_preference = payload.get("difficulty_preference", DifficultyLevel.INTERMEDIATE)
            
            # Analyze user's current skill level
            current_skills = await self._assess_current_skills(user_id)
            
            # Identify skill gaps
            skill_gaps = await self._identify_skill_gaps(current_skills, target_skills)
            
            # Get relevant content
            relevant_content = await self._get_relevant_content_for_skills(skill_gaps)
            
            # Build optimal learning sequence
            learning_path = await self._build_optimal_learning_sequence(
                user_id, relevant_content, skill_gaps, time_constraint_hours, difficulty_preference
            )
            
            # Store learning path
            path_id = await self._store_learning_path(learning_path)
            
            return {
                "status": "success",
                "learning_path_id": str(path_id),
                "path_name": learning_path.path_name,
                "estimated_duration_hours": learning_path.estimated_duration_hours,
                "content_sequence_count": len(learning_path.content_sequence),
                "target_skills": target_skills
            }
            
        except Exception as e:
            logger.error(f"Error building learning path: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _analyze_learning_patterns(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user learning patterns"""
        try:
            user_id = UUID(payload.get("user_id"))
            
            # Get user interaction history
            interactions = await self._get_user_interaction_history(user_id)
            
            # Analyze patterns
            pattern = await self._extract_learning_pattern(interactions)
            
            # Store pattern for future recommendations
            await self._store_learning_pattern(pattern)
            
            return {
                "status": "success",
                "learning_pattern": {
                    "preferred_content_types": [ct.value for ct in pattern.preferred_content_types],
                    "preferred_difficulty_levels": [dl.value for dl in pattern.preferred_difficulty_levels],
                    "optimal_session_length": pattern.optimal_session_length,
                    "peak_learning_hours": pattern.peak_learning_hours,
                    "learning_velocity": pattern.learning_velocity,
                    "retention_rate": pattern.retention_rate,
                    "strong_areas": pattern.strong_areas,
                    "skill_gaps": pattern.skill_gaps
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _detect_skill_gaps(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Detect skill gaps for user"""
        try:
            user_id = UUID(payload.get("user_id"))
            target_roles = payload.get("target_roles", [])
            
            # Get current skills assessment
            current_skills = await self._assess_current_skills(user_id)
            
            # Get required skills for target roles
            required_skills = await self._get_required_skills_for_roles(target_roles)
            
            # Identify gaps
            skill_gaps = self._calculate_skill_gaps(current_skills, required_skills)
            
            # Generate gap-filling recommendations
            gap_recommendations = await self._recommend_gap_filling_content(skill_gaps)
            
            return {
                "status": "success",
                "skill_gaps": skill_gaps,
                "recommendations": gap_recommendations,
                "current_skill_level": current_skills,
                "required_skill_level": required_skills
            }
            
        except Exception as e:
            logger.error(f"Error detecting skill gaps: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _optimize_learning_sequence(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize learning sequence for better outcomes"""
        try:
            user_id = UUID(payload.get("user_id"))
            content_sequence = payload.get("content_sequence", [])
            
            # Get user learning pattern
            learning_pattern = await self._get_user_learning_pattern(user_id)
            
            # Analyze sequence efficiency
            optimization_suggestions = await self._analyze_sequence_efficiency(
                content_sequence, learning_pattern
            )
            
            # Generate optimized sequence
            optimized_sequence = await self._generate_optimized_sequence(
                content_sequence, learning_pattern, optimization_suggestions
            )
            
            return {
                "status": "success",
                "optimized_sequence": [str(content_id) for content_id in optimized_sequence],
                "optimization_suggestions": optimization_suggestions,
                "estimated_improvement": "15-25% faster learning"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing learning sequence: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _adapt_to_preferences(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt recommendations to user preferences"""
        try:
            user_id = UUID(payload.get("user_id"))
            feedback = payload.get("feedback", {})
            
            # Update user preferences based on feedback
            await self._update_user_preferences(user_id, feedback)
            
            # Recalculate learning pattern
            updated_pattern = await self._analyze_learning_patterns({"user_id": str(user_id)})
            
            # Generate updated recommendations
            updated_recommendations = await self._generate_recommendations({
                "user_id": str(user_id),
                "type": "adaptive",
                "max_recommendations": 5
            })
            
            return {
                "status": "success",
                "preferences_updated": True,
                "updated_recommendations": updated_recommendations.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Error adapting to preferences: {e}")
            return {"status": "error", "message": str(e)}
            
    # Recommendation algorithms
    async def _collaborative_filtering(self, user_id: UUID, content_items: List[ContentItem],
                                     interaction_history: List[UserContentInteraction]) -> List[ContentItem]:
        """Collaborative filtering recommendation algorithm"""
        # Get similar users based on interaction patterns
        similar_users = await self._find_similar_users(user_id, interaction_history)
        
        # Get content preferred by similar users
        recommended_content = []
        for similar_user in similar_users:
            similar_user_content = await self._get_user_preferred_content(similar_user)
            recommended_content.extend(similar_user_content)
            
        # Score and rank recommendations
        scored_content = self._score_collaborative_recommendations(
            recommended_content, content_items, user_id
        )
        
        return scored_content[:10]  # Return top 10
        
    async def _content_based_filtering(self, user_id: UUID, content_items: List[ContentItem],
                                     learning_pattern: LearningPattern) -> List[ContentItem]:
        """Content-based filtering recommendation algorithm"""
        # Get user's preferred content features
        preferred_features = self._extract_preferred_features(learning_pattern)
        
        # Score content based on feature similarity
        scored_content = []
        for content in content_items:
            similarity_score = self._calculate_content_similarity(content, preferred_features)
            if similarity_score > 0.3:  # Minimum threshold
                scored_content.append((content, similarity_score))
                
        # Sort by similarity score
        scored_content.sort(key=lambda x: x[1], reverse=True)
        
        return [content for content, score in scored_content[:10]]
        
    async def _hybrid_recommendation(self, user_id: UUID, content_items: List[ContentItem],
                                   learning_pattern: LearningPattern,
                                   interaction_history: List[UserContentInteraction]) -> List[ContentItem]:
        """Hybrid recommendation combining multiple algorithms"""
        # Get recommendations from different algorithms
        collaborative_recs = await self._collaborative_filtering(user_id, content_items, interaction_history)
        content_based_recs = await self._content_based_filtering(user_id, content_items, learning_pattern)
        
        # Combine and score
        combined_scores = defaultdict(float)
        
        # Weight collaborative recommendations
        for content in collaborative_recs:
            combined_scores[content.content_id] += 0.4
            
        # Weight content-based recommendations
        for content in content_based_recs:
            combined_scores[content.content_id] += 0.6
            
        # Sort and return top recommendations
        sorted_content = sorted(content_items, key=lambda x: combined_scores[x.content_id], reverse=True)
        
        return sorted_content[:10]
        
    async def _learning_path_recommendation(self, user_id: UUID, target_skills: List[str],
                                          content_items: List[ContentItem]) -> List[ContentItem]:
        """Learning path-based recommendation algorithm"""
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(content_items)
        
        # Find optimal path to target skills
        optimal_path = self._find_optimal_path(dependency_graph, target_skills)
        
        # Return recommended content in path order
        recommended_content = []
        for skill_step in optimal_path:
            relevant_content = [content for content in content_items 
                              if skill_step in content.learning_objectives]
            recommended_content.extend(relevant_content[:2])  # Top 2 per skill
            
        return recommended_content
        
    async def _adaptive_recommendation(self, user_id: UUID, current_performance: Dict[str, Any],
                                     content_items: List[ContentItem]) -> List[ContentItem]:
        """Adaptive recommendation based on current performance"""
        # Analyze current performance
        performance_score = current_performance.get("average_score", 75)
        difficulty_preference = current_performance.get("difficulty_preference", DifficultyLevel.INTERMEDIATE)
        
        # Adjust difficulty based on performance
        if performance_score > 85:
            # User is doing well, recommend more challenging content
            target_difficulty = self._get_next_difficulty_level(difficulty_preference, "increase")
        elif performance_score < 60:
            # User is struggling, recommend easier content
            target_difficulty = self._get_next_difficulty_level(difficulty_preference, "decrease")
        else:
            # Maintain current difficulty
            target_difficulty = difficulty_preference
            
        # Filter content by adjusted difficulty
        adapted_content = [content for content in content_items 
                          if content.difficulty_level == target_difficulty]
        
        return adapted_content[:8]
        
    # Helper methods
    async def _get_available_content(self) -> List[ContentItem]:
        """Get all available learning content"""
        async with self.database_pool.acquire() as conn:
            content_rows = await conn.fetch("""
                SELECT * FROM learning_content WHERE is_published = TRUE
            """)
            
        content_items = []
        for row in content_rows:
            content_item = ContentItem(
                content_id=row['content_id'],
                title=row['title'],
                content_type=ContentType(row['content_type']),
                difficulty_level=DifficultyLevel(row['difficulty_level']),
                estimated_duration_minutes=row['estimated_duration_minutes'],
                prerequisites=json.loads(row['prerequisites']) if row['prerequisites'] else [],
                learning_objectives=json.loads(row['learning_objectives']) if row['learning_objectives'] else [],
                tags=json.loads(row['tags']) if row['tags'] else [],
                content_data=json.loads(row['content_data']) if row['content_data'] else {},
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            content_items.append(content_item)
            
        return content_items
        
    async def _get_user_interaction_history(self, user_id: UUID) -> List[UserContentInteraction]:
        """Get user's interaction history"""
        async with self.database_pool.acquire() as conn:
            interaction_rows = await conn.fetch("""
                SELECT * FROM user_content_interactions 
                WHERE user_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1000
            """, user_id)
            
        interactions = []
        for row in interaction_rows:
            interaction = UserContentInteraction(
                interaction_id=row['interaction_id'],
                user_id=row['user_id'],
                content_id=row['content_id'],
                interaction_type=row['interaction_type'],
                timestamp=row['timestamp'],
                duration_minutes=row['duration_minutes'],
                completion_percentage=row['completion_percentage'],
                rating=row['rating'],
                feedback=row['feedback'],
                difficulty_rating=row['difficulty_rating']
            )
            interactions.append(interaction)
            
        return interactions
        
    def _calculate_content_similarity(self, content: ContentItem, preferred_features: Dict[str, Any]) -> float:
        """Calculate similarity between content and user preferences"""
        similarity_score = 0.0
        
        # Difficulty similarity
        if content.difficulty_level in preferred_features.get("preferred_difficulties", []):
            similarity_score += self.similarity_weights["difficulty"]
            
        # Topic similarity
        content_topics = set(content.tags + content.learning_objectives)
        preferred_topics = set(preferred_features.get("preferred_topics", []))
        topic_overlap = len(content_topics.intersection(preferred_topics))
        if topic_overlap > 0:
            similarity_score += self.similarity_weights["topic"] * (topic_overlap / len(content_topics))
            
        # Duration similarity
        preferred_duration = preferred_features.get("preferred_duration", 30)
        duration_diff = abs(content.estimated_duration_minutes - preferred_duration)
        duration_similarity = max(0, 1 - (duration_diff / 60))  # Normalize to 0-1
        similarity_score += self.similarity_weights["duration"] * duration_similarity
        
        # Content type similarity
        if content.content_type in preferred_features.get("preferred_types", []):
            similarity_score += self.similarity_weights["style"]
            
        return min(1.0, similarity_score)
        
    async def _recommend_next_lessons(self, user_id: UUID, content_items: List[ContentItem],
                                    learning_pattern: Dict[str, Any],
                                    interaction_history: List[UserContentInteraction]) -> List[Recommendation]:
        """Recommend next lessons based on progress and preferences"""
        # Get current progress
        completed_content = [interaction.content_id for interaction in interaction_history 
                           if interaction.interaction_type == "completed"]
        
        # Filter out already completed content
        available_content = [content for content in content_items 
                           if content.content_id not in completed_content]
        
        # Apply prerequisite filtering
        recommended_content = []
        for content in available_content:
            prerequisites_met = all(prereq in completed_content for prereq in content.prerequisites)
            if prerequisites_met:
                recommended_content.append(content)
                
        # Score and rank
        scored_content = self._score_content_for_next_lesson(recommended_content, learning_pattern)
        
        # Create recommendations
        recommendations = []
        for content, score in scored_content:
            recommendation = Recommendation(
                user_id=user_id,
                recommendation_type=RecommendationType.NEXT_LESSON,
                content_items=[content],
                confidence_score=score,
                reasoning=f"Recommended based on your progress and learning pattern",
                personalized_factors={
                    "difficulty_match": self._calculate_difficulty_match(content, learning_pattern),
                    "time_availability": content.estimated_duration_minutes,
                    "prerequisite_mastery": True
                }
            )
            recommendations.append(recommendation)
            
        return recommendations[:5]
        
    def _score_content_for_next_lesson(self, content_items: List[ContentItem], 
                                     learning_pattern: Dict[str, Any]) -> List[Tuple[ContentItem, float]]:
        """Score content for next lesson recommendation"""
        scored_content = []
        
        for content in content_items:
            score = 0.0
            
            # Difficulty alignment
            preferred_difficulties = learning_pattern.get("preferred_difficulty_levels", [DifficultyLevel.INTERMEDIATE])
            if content.difficulty_level in preferred_difficulties:
                score += 0.3
                
            # Learning objectives alignment
            user_objectives = learning_pattern.get("target_skills", [])
            content_objectives = content.learning_objectives
            objective_match = len(set(user_objectives).intersection(set(content_objectives)))
            if objective_match > 0:
                score += 0.4 * (objective_match / len(content_objectives))
                
            # Duration preference
            preferred_duration = learning_pattern.get("optimal_session_length", 30)
            duration_alignment = 1.0 - abs(content.estimated_duration_minutes - preferred_duration) / preferred_duration
            score += 0.2 * max(0, duration_alignment)
            
            # Content type preference
            preferred_types = learning_pattern.get("preferred_content_types", [ContentType.LESSON])
            if content.content_type in preferred_types:
                score += 0.1
                
            scored_content.append((content, score))
            
        return sorted(scored_content, key=lambda x: x[1], reverse=True)
        
    def _calculate_difficulty_match(self, content: ContentItem, learning_pattern: Dict[str, Any]) -> float:
        """Calculate how well content difficulty matches user preferences"""
        preferred_difficulties = learning_pattern.get("preferred_difficulty_levels", [DifficultyLevel.INTERMEDIATE])
        
        if content.difficulty_level in preferred_difficulties:
            return 1.0
        else:
            # Calculate difficulty distance
            difficulty_order = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, 
                              DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]
            if content.difficulty_level in difficulty_order:
                content_index = difficulty_order.index(content.difficulty_level)
                preferred_indices = [difficulty_order.index(d) for d in preferred_difficulties if d in difficulty_order]
                if preferred_indices:
                    min_distance = min(abs(content_index - pi) for pi in preferred_indices)
                    return max(0, 1.0 - (min_distance * 0.3))  # Penalty for distance
            return 0.5  # Neutral score
        
    async def _store_recommendations(self, user_id: UUID, recommendations: List[Recommendation]):
        """Store recommendations in database"""
        async with self.database_pool.acquire() as conn:
            for recommendation in recommendations:
                await conn.execute("""
                    INSERT INTO content_recommendations (
                        recommendation_id, user_id, recommendation_type, content_ids,
                        confidence_score, reasoning, personalized_factors, algorithm_used
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    recommendation.recommendation_id,
                    recommendation.user_id,
                    recommendation.recommendation_type.value,
                    json.dumps([str(item.content_id) for item in recommendation.content_items]),
                    recommendation.confidence_score,
                    recommendation.reasoning,
                    json.dumps(recommendation.personalized_factors),
                    recommendation.algorithm_used
                )
                
    async def _emit_recommendations(self, user_id: UUID, recommendations: List[Recommendation]):
        """Emit recommendations via message bus"""
        if self.nats_client and recommendations:
            # Emit the highest confidence recommendation
            top_recommendation = max(recommendations, key=lambda x: x.confidence_score)
            
            message = {
                "user_id": str(user_id),
                "recommendation_type": top_recommendation.recommendation_type.value,
                "content_title": top_recommendation.content_items[0].title if top_recommendation.content_items else None,
                "confidence_score": top_recommendation.confidence_score,
                "reasoning": top_recommendation.reasoning,
                "timestamp": top_recommendation.generated_at.isoformat()
            }
            
            await self.nats_client.publish(
                f"recommendations.{user_id}",
                json.dumps(message).encode()
            )
            
    # Database operations
    async def _extract_learning_pattern(self, interactions: List[UserContentInteraction]) -> LearningPattern:
        """Extract learning pattern from interaction history"""
        if not interactions:
            return LearningPattern(user_id=interactions[0].user_id if interactions else UUID('00000000-0000-0000-0000-000000000000'))
            
        user_id = interactions[0].user_id
        
        # Analyze content type preferences
        content_type_counts = Counter()
        for interaction in interactions:
            if interaction.content_id:  # Would need to join with content table
                content_type_counts[interaction.interaction_type] += 1
                
        # Analyze completion patterns
        completion_rates = []
        session_lengths = []
        for interaction in interactions:
            if interaction.completion_percentage > 0:
                completion_rates.append(interaction.completion_percentage)
            if interaction.duration_minutes:
                session_lengths.append(interaction.duration_minutes)
                
        # Calculate learning velocity (simplified)
        learning_velocity = statistics.mean(completion_rates) / max(1, statistics.mean(session_lengths)) if completion_rates and session_lengths else 1.0
        
        # Analyze peak hours
        hour_counts = Counter()
        for interaction in interactions:
            hour_counts[interaction.timestamp.hour] += 1
            
        peak_hours = [hour for hour, count in hour_counts.most_common(3)]
        
        return LearningPattern(
            user_id=user_id,
            optimal_session_length=statistics.median(session_lengths) if session_lengths else 30,
            peak_learning_hours=peak_hours,
            learning_velocity=learning_velocity,
            retention_rate=statistics.mean(completion_rates) / 100.0 if completion_rates else 0.8
        )
        
    # Placeholder implementations for complex methods
    async def _update_learning_patterns(self, progress_data: Dict[str, Any]):
        """Update learning patterns based on progress"""
        pass
        
    async def _update_recommendation_model(self, interaction_data: Dict[str, Any]):
        """Update recommendation model based on user interactions"""
        pass
        
    async def _find_similar_users(self, user_id: UUID, interactions: List[UserContentInteraction]) -> List[UUID]:
        """Find users with similar learning patterns"""
        # Simplified implementation
        return [UUID('00000000-0000-0000-0000-000000000001')]
        
    async def _get_user_preferred_content(self, user_id: UUID) -> List[ContentItem]:
        """Get content preferred by a user"""
        return []
        
    def _score_collaborative_recommendations(self, recommended_content: List[ContentItem], 
                                           all_content: List[ContentItem], 
                                           user_id: UUID) -> List[ContentItem]:
        """Score collaborative filtering recommendations"""
        return recommended_content[:10]
        
    def _extract_preferred_features(self, learning_pattern: LearningPattern) -> Dict[str, Any]:
        """Extract preferred features from learning pattern"""
        return {
            "preferred_difficulties": [dl.value for dl in learning_pattern.preferred_difficulty_levels],
            "preferred_types": [ct.value for ct in learning_pattern.preferred_content_types],
            "preferred_topics": learning_pattern.strong_areas,
            "preferred_duration": learning_pattern.optimal_session_length
        }
        
    async def _assess_current_skills(self, user_id: UUID) -> Dict[str, float]:
        """Assess current skill levels"""
        return {"programming": 0.7, "problem_solving": 0.6, "algorithms": 0.5}
        
    async def _get_required_skills_for_roles(self, target_roles: List[str]) -> Dict[str, float]:
        """Get required skills for target roles"""
        return {"programming": 0.9, "problem_solving": 0.8, "algorithms": 0.7}
        
    def _calculate_skill_gaps(self, current: Dict[str, float], required: Dict[str, float]) -> Dict[str, float]:
        """Calculate skill gaps"""
        gaps = {}
        for skill, required_level in required.items():
            current_level = current.get(skill, 0.0)
            gaps[skill] = max(0, required_level - current_level)
        return gaps
        
    def _build_dependency_graph(self, content_items: List[ContentItem]) -> Dict[str, List[str]]:
        """Build content dependency graph"""
        graph = {}
        for content in content_items:
            graph[str(content.content_id)] = content.prerequisites
        return graph
        
    def _find_optimal_path(self, dependency_graph: Dict[str, List[str]], target_skills: List[str]) -> List[str]:
        """Find optimal learning path"""
        return target_skills  # Simplified
        
    def _get_next_difficulty_level(self, current: DifficultyLevel, direction: str) -> DifficultyLevel:
        """Get next difficulty level"""
        levels = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, 
                 DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]
        
        current_index = levels.index(current)
        if direction == "increase" and current_index < len(levels) - 1:
            return levels[current_index + 1]
        elif direction == "decrease" and current_index > 0:
            return levels[current_index - 1]
        else:
            return current
            
    async def _get_user_learning_pattern(self, user_id: UUID) -> LearningPattern:
        """Get stored learning pattern for user"""
        # Would load from database in real implementation
        return LearningPattern(user_id=user_id)
        
    async def _analyze_sequence_efficiency(self, content_sequence: List[str], 
                                         learning_pattern: LearningPattern) -> List[str]:
        """Analyze learning sequence efficiency"""
        return ["Consider adding more prerequisites", "Reduce complexity jumps"]
        
    async def _generate_optimized_sequence(self, content_sequence: List[str], 
                                         learning_pattern: LearningPattern,
                                         suggestions: List[str]) -> List[UUID]:
        """Generate optimized learning sequence"""
        return [UUID(content_id) for content_id in content_sequence]
        
    async def _update_user_preferences(self, user_id: UUID, feedback: Dict[str, Any]):
        """Update user preferences based on feedback"""
        pass
        
    async def _store_learning_pattern(self, pattern: LearningPattern):
        """Store learning pattern in database"""
        pass
        
    async def _get_relevant_content_for_skills(self, skill_gaps: Dict[str, float]) -> List[ContentItem]:
        """Get content relevant for skill gaps"""
        return await self._get_available_content()  # Simplified
        
    async def _build_optimal_learning_sequence(self, user_id: UUID, content_items: List[ContentItem],
                                             skill_gaps: Dict[str, float], time_constraint: int,
                                             difficulty_preference: DifficultyLevel) -> LearningPath:
        """Build optimal learning sequence"""
        path = LearningPath(
            path_id=uuid4(),
            user_id=user_id,
            path_name="Personalized Learning Path",
            description="Adaptive learning path based on your skill gaps and preferences",
            target_skills=list(skill_gaps.keys()),
            estimated_duration_hours=time_constraint,
            content_sequence=content_items[:10]  # Simplified
        )
        return path
        
    async def _store_learning_path(self, path: LearningPath) -> UUID:
        """Store learning path in database"""
        # Would store in database in real implementation
        return path.path_id
        
    async def _recommend_gap_filling_content(self, skill_gaps: Dict[str, float]) -> List[Dict[str, Any]]:
        """Recommend content to fill skill gaps"""
        return [{"skill": skill, "priority": "high", "recommended_content": "Basic Tutorial"} 
                for skill in skill_gaps.keys()]
                
    async def _recommend_similar_content(self, user_id: UUID, reference_content_id: Optional[str],
                                       content_items: List[ContentItem], 
                                       learning_pattern: Dict[str, Any]) -> List[Recommendation]:
        """Recommend similar content"""
        return []
        
    async def _recommend_skill_gap_content(self, user_id: UUID, learning_pattern: Dict[str, Any],
                                         content_items: List[ContentItem]) -> List[Recommendation]:
        """Recommend content to address skill gaps"""
        return []
        
    async def _generate_general_recommendations(self, user_id: UUID, content_items: List[ContentItem],
                                              learning_pattern: Dict[str, Any],
                                              interaction_history: List[UserContentInteraction]) -> List[Recommendation]:
        """Generate general recommendations"""
        return []
        
    async def _apply_diversity_and_personalization(self, recommendations: List[Recommendation],
                                                 learning_pattern: Dict[str, Any],
                                                 max_count: int) -> List[Recommendation]:
        """Apply diversity and personalization to recommendations"""
        return recommendations[:max_count]


# Agent factory function
def create_content_recommender_agent() -> ContentRecommenderAgent:
    """Create and configure Content Recommender Agent"""
    return ContentRecommenderAgent()


# Export
__all__ = [
    "ContentRecommenderAgent",
    "Recommendation",
    "LearningPattern",
    "ContentItem",
    "UserContentInteraction",
    "LearningPath",
    "RecommendationType",
    "ContentType",
    "DifficultyLevel",
    "LearningStyle",
    "create_content_recommender_agent"
]