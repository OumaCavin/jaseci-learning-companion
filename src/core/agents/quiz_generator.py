"""
Quiz Generator Agent (byLLM Integration)
AI-powered adaptive quiz generation for the Jaseci Learning Companion

This agent uses Jaseci's byLLM decorator to generate intelligent, adaptive
quizzes based on user progress, learning patterns, and content difficulty.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import random
from enum import Enum

import asyncpg
import redis.asyncio as redis
import nats
from pydantic import BaseModel, Field, validator
import jaseci
from jaseci import Jac

from ..registry import Agent, AgentMetadata, AgentType, AgentStatus, Priority, AgentTask


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models for Quiz Generation
class QuestionType(str, Enum):
    """Question types for adaptive quizzes"""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_BLANK = "fill_in_blank"
    CODE_COMPLETION = "code_completion"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    CODE_EXECUTION = "code_execution"


class DifficultyLevel(str, Enum):
    """Difficulty levels for adaptive quizzes"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Question(BaseModel):
    """Individual quiz question"""
    question_id: UUID = Field(default_factory=uuid4)
    question_type: QuestionType
    difficulty: DifficultyLevel
    title: str
    question_text: str
    options: List[str] = Field(default_factory=list)  # For multiple choice
    correct_answer: str
    explanation: str
    hints: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    concepts_tested: List[str] = Field(default_factory=list)
    estimated_time_seconds: int = 60
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Quiz(BaseModel):
    """Complete quiz with adaptive questions"""
    quiz_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    
    # Quiz metadata
    title: str
    description: str
    quiz_type: str = "adaptive"  # adaptive, diagnostic, practice, assessment
    total_questions: int
    time_limit_minutes: Optional[int] = None
    passing_score: float = 70.0
    
    # Questions
    questions: List[Question] = Field(default_factory=list)
    question_order: List[UUID] = Field(default_factory=list)
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generation_prompt: Optional[str] = None
    adaptive_criteria: Dict[str, Any] = Field(default_factory=dict)
    difficulty_adjustments: List[str] = Field(default_factory=list)


class QuizResponse(BaseModel):
    """User response to quiz question"""
    response_id: UUID = Field(default_factory=uuid4)
    quiz_id: UUID
    question_id: UUID
    user_id: UUID
    
    # Response data
    user_answer: str
    is_correct: bool
    time_taken_seconds: int
    attempts: int = 1
    
    # AI-generated feedback
    ai_feedback: Optional[str] = None
    helpfulness_score: Optional[float] = None
    explanation_quality: Optional[float] = None
    
    timestamps
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None


class QuizAnalytics(BaseModel):
    """Analytics for quiz performance"""
    quiz_id: UUID
    user_id: UUID
    
    # Performance metrics
    total_questions: int
    correct_answers: int
    accuracy_percentage: float
    average_time_per_question: float
    
    # Adaptive adjustments
    initial_difficulty: DifficultyLevel
    final_difficulty: DifficultyLevel
    difficulty_adjustments_made: int
    adaptive_effectiveness: float  # How well the adaptation worked
    
    # Learning insights
    weak_concepts_identified: List[str]
    strong_concepts_confirmed: List[str]
    recommended_review_topics: List[str]
    
    timestamps
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdaptiveParameters(BaseModel):
    """Parameters for adaptive quiz generation"""
    user_id: UUID
    current_skill_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objectives: List[str] = Field(default_factory=list)
    
    # Adaptive thresholds
    correct_answer_threshold: float = 0.8
    time_efficiency_threshold: float = 0.7
    
    # Question preferences
    preferred_question_types: List[QuestionType] = Field(default_factory=list)
    avoid_question_types: List[QuestionType] = Field(default_factory=list)
    
    # Difficulty progression
    difficulty_progression_factor: float = 0.1  # How much to adjust per question
    
    # Learning context
    recently_studied_topics: List[str] = Field(default_factory=list)
    struggling_concepts: List[str] = Field(default_factory=list)
    mastered_concepts: List[str] = Field(default_factory=list)


class QuizGeneratorAgent(Agent):
    """AI-powered Quiz Generator Agent with byLLM integration"""
    
    def __init__(self):
        super().__init__(
            agent_id=uuid4(),
            agent_type=AgentType.QUIZ_GENERATOR,
            name="AI Quiz Generator",
            version="2.0.0-enterprise"
        )
        self.redis_client = None
        self.database_pool = None
        self.nats_client = None
        
        # byLLM configurations
        self.llm_models = {
            "question_generation": "gpt-4",  # For generating questions
            "difficulty_assessment": "gpt-3.5-turbo",  # For assessing difficulty
            "feedback_generation": "gpt-3.5-turbo"  # For generating feedback
        }
        
        # Quiz templates for different concepts
        self.quiz_templates = self._load_quiz_templates()
        
    async def initialize(self) -> bool:
        """Initialize the Quiz Generator Agent"""
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
            await self.register_capability("generate_adaptive_quiz")
            await self.register_capability("assess_question_difficulty")
            await self.register_capability("generate_ai_feedback")
            await self.register_capability("adapt_quiz_difficulty")
            await self.register_capability("analyze_quiz_performance")
            
            # Subscribe to NATS subjects
            await self.nats_client.subscribe("quiz.requests.*", self._handle_quiz_request)
            await self.nats_client.subscribe("progress.updates.*", self._handle_progress_update)
            
            logger.info("Quiz Generator Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Quiz Generator Agent: {e}")
            return False
            
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process quiz generation tasks"""
        try:
            task_type = task.task_type
            
            if task_type == "generate_quiz":
                return await self._generate_adaptive_quiz(task.payload)
            elif task_type == "assess_difficulty":
                return await self._assess_question_difficulty(task.payload)
            elif task_type == "generate_feedback":
                return await self._generate_ai_feedback(task.payload)
            elif task_type == "adapt_quiz":
                return await self._adapt_quiz_difficulty(task.payload)
            elif task_type == "analyze_performance":
                return await self._analyze_quiz_performance(task.payload)
            elif task_type == "get_quiz_templates":
                return await self._get_quiz_templates(task.payload)
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
                "templates_loaded": len(self.quiz_templates),
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
            
    # byLLM decorated methods for AI integration
    @Jac.byLLM(
        model="gpt-4",
        prompt_template="""
        Generate a Jaseci programming quiz question based on the following parameters:
        
        Topic: {topic}
        Difficulty: {difficulty}
        Question Type: {question_type}
        Learning Objectives: {learning_objectives}
        
        Generate a high-quality question that tests understanding of {topic} concepts.
        Ensure the difficulty matches the specified level.
        
        Return JSON with:
        {{
            "title": "Question title",
            "question_text": "The actual question",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],  # if multiple choice
            "correct_answer": "Correct answer",
            "explanation": "Detailed explanation of the answer",
            "hints": ["Hint 1", "Hint 2"],  # Optional hints
            "concepts_tested": ["concept1", "concept2"],
            "estimated_time_seconds": 60
        }}
        """,
        max_tokens=500,
        temperature=0.7
    )
    async def generate_question_with_byllm(self, topic: str, difficulty: DifficultyLevel, 
                                         question_type: QuestionType, 
                                         learning_objectives: List[str]) -> Dict[str, Any]:
        """Generate quiz question using byLLM decorator"""
        # This method will be automatically enhanced by the byLLM decorator
        # The actual AI call will be handled by Jaseci
        pass
        
    @Jac.byLLM(
        model="gpt-3.5-turbo",
        prompt_template="""
        Assess the difficulty level of the following Jaseci programming question:
        
        Question: {question_text}
        Concepts: {concepts}
        
        Consider the complexity of the concepts, required background knowledge,
        and typical solution complexity.
        
        Return JSON:
        {{
            "difficulty": "beginner|intermediate|advanced|expert",
            "reasoning": "Explanation of difficulty assessment",
            "prerequisites": ["prerequisite1", "prerequisite2"],
            "cognitive_load": "low|medium|high"
        }}
        """,
        max_tokens=300,
        temperature=0.3
    )
    async def assess_difficulty_with_byllm(self, question_text: str, concepts: List[str]) -> Dict[str, Any]:
        """Assess question difficulty using byLLM decorator"""
        pass
        
    @Jac.byLLM(
        model="gpt-3.5-turbo",
        prompt_template="""
        Generate personalized feedback for a Jaseci quiz response:
        
        Question: {question_text}
        User Answer: {user_answer}
        Correct Answer: {correct_answer}
        Explanation: {explanation}
        User Performance: {performance_metrics}
        
        Provide helpful, encouraging feedback that:
        1. Explains the correct answer
        2. Identifies learning opportunities
        3. Offers specific improvement suggestions
        4. Maintains a positive, supportive tone
        
        Return JSON:
        {{
            "feedback": "Personalized feedback text",
            "learning_point": "Key concept to focus on",
            "next_steps": ["Step 1", "Step 2"],
            "encouragement": "Motivational message"
        }}
        """,
        max_tokens=400,
        temperature=0.8
    )
    async def generate_feedback_with_byllm(self, question_text: str, user_answer: str, 
                                         correct_answer: str, explanation: str,
                                         performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI feedback using byLLM decorator"""
        pass
        
    # Event handlers
    async def _handle_quiz_request(self, msg):
        """Handle quiz request events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._generate_adaptive_quiz(data)
        except Exception as e:
            logger.error(f"Error handling quiz request: {e}")
            
    async def _handle_progress_update(self, msg):
        """Handle progress updates for adaptive quiz generation"""
        try:
            data = json.loads(msg.data.decode())
            # Update user skill assessment based on progress
            await self._update_user_skill_assessment(data)
        except Exception as e:
            logger.error(f"Error handling progress update: {e}")
            
    # Main processing methods
    async def _generate_adaptive_quiz(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate adaptive quiz using byLLM"""
        try:
            # Parse adaptive parameters
            adaptive_params = AdaptiveParameters(**payload)
            
            # Get user learning profile
            user_profile = await self._get_user_learning_profile(adaptive_params.user_id)
            
            # Determine quiz parameters
            quiz_params = await self._determine_quiz_parameters(adaptive_params, user_profile)
            
            # Generate questions using byLLM
            questions = []
            for i in range(quiz_params["total_questions"]):
                question = await self._generate_single_question(
                    adaptive_params, user_profile, i, quiz_params
                )
                if question:
                    questions.append(question)
                    
            # Create quiz object
            quiz = Quiz(
                user_id=adaptive_params.user_id,
                course_id=payload.get("course_id"),
                lesson_id=payload.get("lesson_id"),
                title=quiz_params["title"],
                description=quiz_params["description"],
                total_questions=len(questions),
                questions=questions,
                adaptive_criteria=adaptive_params.dict(),
                generation_prompt=json.dumps(quiz_params)
            )
            
            # Store quiz in database
            quiz_id = await self._store_quiz(quiz)
            
            # Cache quiz for quick access
            await self.redis_client.setex(
                f"quiz:{quiz_id}",
                3600,  # 1 hour cache
                json.dumps(quiz.dict(), default=str)
            )
            
            logger.info(f"Generated adaptive quiz {quiz_id} with {len(questions)} questions")
            
            return {
                "status": "success",
                "quiz_id": str(quiz_id),
                "total_questions": len(questions),
                "estimated_time": sum(q.estimated_time_seconds for q in questions) // 60,
                "difficulty_range": f"{quiz_params['min_difficulty']} to {quiz_params['max_difficulty']}"
            }
            
        except Exception as e:
            logger.error(f"Error generating adaptive quiz: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _assess_question_difficulty(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Assess question difficulty using byLLM"""
        try:
            question_text = payload.get("question_text")
            concepts = payload.get("concepts", [])
            
            # Use byLLM to assess difficulty
            difficulty_assessment = await self.assess_difficulty_with_byllm(question_text, concepts)
            
            return {
                "status": "success",
                "assessment": difficulty_assessment,
                "question_text": question_text
            }
            
        except Exception as e:
            logger.error(f"Error assessing difficulty: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _generate_ai_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI feedback using byLLM"""
        try:
            # Extract parameters
            question_text = payload.get("question_text")
            user_answer = payload.get("user_answer")
            correct_answer = payload.get("correct_answer")
            explanation = payload.get("explanation", "")
            performance_metrics = payload.get("performance_metrics", {})
            
            # Use byLLM to generate feedback
            feedback = await self.generate_feedback_with_byllm(
                question_text, user_answer, correct_answer, explanation, performance_metrics
            )
            
            return {
                "status": "success",
                "feedback": feedback,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _adapt_quiz_difficulty(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt quiz difficulty based on performance"""
        try:
            quiz_id = UUID(payload.get("quiz_id"))
            user_responses = payload.get("responses", [])
            
            # Analyze performance so far
            performance_analysis = await self._analyze_performance_so_far(user_responses)
            
            # Determine difficulty adjustments
            adjustments = await self._determine_difficulty_adjustments(performance_analysis)
            
            # Apply adjustments to remaining questions
            adapted_questions = await self._apply_difficulty_adjustments(quiz_id, adjustments)
            
            return {
                "status": "success",
                "adjustments": adjustments,
                "adapted_questions_count": len(adapted_questions),
                "new_difficulty_level": adjustments.get("target_difficulty")
            }
            
        except Exception as e:
            logger.error(f"Error adapting quiz difficulty: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _analyze_quiz_performance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete quiz performance"""
        try:
            quiz_id = UUID(payload.get("quiz_id"))
            user_id = UUID(payload.get("user_id"))
            
            # Get quiz and responses
            quiz = await self._get_quiz(quiz_id)
            responses = await self._get_quiz_responses(quiz_id, user_id)
            
            # Calculate analytics
            analytics = await self._calculate_quiz_analytics(quiz, responses)
            
            # Store analytics
            await self._store_quiz_analytics(analytics)
            
            # Generate learning insights
            insights = await self._generate_learning_insights(analytics)
            
            return {
                "status": "success",
                "analytics": analytics.dict(),
                "insights": insights,
                "quiz_id": str(quiz_id)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing quiz performance: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_quiz_templates(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get available quiz templates"""
        try:
            concept = payload.get("concept", "")
            
            if concept in self.quiz_templates:
                templates = self.quiz_templates[concept]
            else:
                templates = self.quiz_templates["default"]
                
            return {
                "status": "success",
                "concept": concept,
                "templates": templates,
                "total_templates": len(templates)
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz templates: {e}")
            return {"status": "error", "message": str(e)}
            
    # Helper methods
    async def _get_user_learning_profile(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's learning profile for adaptive generation"""
        # Get from database or cache
        async with self.database_pool.acquire() as conn:
            profile = await conn.fetchrow("""
                SELECT * FROM user_learning_profiles WHERE user_id = $1
            """, user_id)
            
        if profile:
            return dict(profile)
        else:
            # Return default profile
            return {
                "skill_level": "intermediate",
                "learning_style": "visual",
                "preferred_difficulty": "challenging",
                "strong_concepts": [],
                "weak_concepts": []
            }
            
    async def _determine_quiz_parameters(self, adaptive_params: AdaptiveParameters, 
                                       user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Determine quiz generation parameters"""
        # Analyze user performance to set parameters
        current_level = adaptive_params.current_skill_level
        num_questions = min(10, max(3, len(adaptive_params.learning_objectives) * 2))
        
        # Determine difficulty range
        difficulty_range = self._get_difficulty_range(current_level)
        
        return {
            "title": f"Adaptive Quiz - {current_level.value.title()}",
            "description": f"Personalized quiz focusing on {', '.join(adaptive_params.learning_objectives)}",
            "total_questions": num_questions,
            "min_difficulty": difficulty_range["min"],
            "max_difficulty": difficulty_range["max"],
            "adaptive_factor": adaptive_params.difficulty_progression_factor
        }
        
    async def _generate_single_question(self, adaptive_params: AdaptiveParameters, 
                                      user_profile: Dict[str, Any], 
                                      question_index: int, 
                                      quiz_params: Dict[str, Any]) -> Optional[Question]:
        """Generate single question using byLLM"""
        try:
            # Determine question difficulty based on performance so far
            target_difficulty = self._calculate_question_difficulty(
                adaptive_params, question_index, quiz_params
            )
            
            # Select question type based on user preferences
            question_type = self._select_question_type(adaptive_params)
            
            # Generate question using byLLM
            topic = random.choice(adaptive_params.learning_objectives)
            
            generated_question = await self.generate_question_with_byllm(
                topic=topic,
                difficulty=target_difficulty,
                question_type=question_type,
                learning_objectives=[topic]
            )
            
            # Create Question object
            question = Question(
                question_type=question_type,
                difficulty=target_difficulty,
                title=generated_question.get("title", f"Question {question_index + 1}"),
                question_text=generated_question.get("question_text", ""),
                options=generated_question.get("options", []),
                correct_answer=generated_question.get("correct_answer", ""),
                explanation=generated_question.get("explanation", ""),
                hints=generated_question.get("hints", []),
                concepts_tested=generated_question.get("concepts_tested", [topic]),
                estimated_time_seconds=generated_question.get("estimated_time_seconds", 60)
            )
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return None
            
    def _calculate_question_difficulty(self, adaptive_params: AdaptiveParameters, 
                                     question_index: int, quiz_params: Dict[str, Any]) -> DifficultyLevel:
        """Calculate appropriate difficulty for question"""
        # Simple adaptive logic - can be enhanced with ML
        base_difficulty = adaptive_params.current_skill_level
        progression = adaptive_params.difficulty_progression_factor * question_index
        
        # Adjust difficulty based on progression
        if progression > 0.2:
            if base_difficulty == DifficultyLevel.BEGINNER:
                return DifficultyLevel.INTERMEDIATE
            elif base_difficulty == DifficultyLevel.INTERMEDIATE:
                return DifficultyLevel.ADVANCED
            elif base_difficulty == DifficultyLevel.ADVANCED:
                return DifficultyLevel.EXPERT
                
        return base_difficulty
        
    def _select_question_type(self, adaptive_params: AdaptiveParameters) -> QuestionType:
        """Select appropriate question type"""
        available_types = [qt for qt in QuestionType 
                         if qt not in adaptive_params.avoid_question_types]
        
        if adaptive_params.preferred_question_types:
            preferred_available = [qt for qt in adaptive_params.preferred_question_types 
                                 if qt in available_types]
            if preferred_available:
                return random.choice(preferred_available)
                
        return random.choice(available_types)
        
    def _get_difficulty_range(self, skill_level: DifficultyLevel) -> Dict[str, DifficultyLevel]:
        """Get appropriate difficulty range for skill level"""
        ranges = {
            DifficultyLevel.BEGINNER: {"min": DifficultyLevel.BEGINNER, "max": DifficultyLevel.INTERMEDIATE},
            DifficultyLevel.INTERMEDIATE: {"min": DifficultyLevel.BEGINNER, "max": DifficultyLevel.ADVANCED},
            DifficultyLevel.ADVANCED: {"min": DifficultyLevel.INTERMEDIATE, "max": DifficultyLevel.EXPERT},
            DifficultyLevel.EXPERT: {"min": DifficultyLevel.ADVANCED, "max": DifficultyLevel.EXPERT}
        }
        return ranges.get(skill_level, ranges[DifficultyLevel.INTERMEDIATE])
        
    async def _store_quiz(self, quiz: Quiz) -> UUID:
        """Store quiz in database"""
        async with self.database_pool.acquire() as conn:
            quiz_id = await conn.fetchval("""
                INSERT INTO adaptive_quizzes (
                    quiz_id, user_id, course_id, lesson_id, title, description,
                    quiz_type, total_questions, questions_data, adaptive_criteria
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING quiz_id
            """,
                quiz.quiz_id, quiz.user_id, quiz.course_id, quiz.lesson_id,
                quiz.title, quiz.description, quiz.quiz_type, quiz.total_questions,
                json.dumps([q.dict() for q in quiz.questions], default=str),
                json.dumps(quiz.adaptive_criteria, default=str)
            )
        return quiz_id
        
    async def _get_quiz(self, quiz_id: UUID) -> Optional[Quiz]:
        """Get quiz from database"""
        async with self.database_pool.acquire() as conn:
            quiz_data = await conn.fetchrow("""
                SELECT * FROM adaptive_quizzes WHERE quiz_id = $1
            """, quiz_id)
            
        if quiz_data:
            # Convert back to Quiz object
            questions_data = json.loads(quiz_data['questions_data'])
            questions = [Question(**q) for q in questions_data]
            
            return Quiz(
                quiz_id=quiz_data['quiz_id'],
                user_id=quiz_data['user_id'],
                course_id=quiz_data['course_id'],
                lesson_id=quiz_data['lesson_id'],
                title=quiz_data['title'],
                description=quiz_data['description'],
                quiz_type=quiz_data['quiz_type'],
                total_questions=quiz_data['total_questions'],
                questions=questions,
                generated_at=quiz_data['generated_at']
            )
        return None
        
    def _load_quiz_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load quiz templates for different Jaseci concepts"""
        return {
            "graph_programming": [
                {
                    "title": "Graph Structure Basics",
                    "concepts": ["nodes", "edges", "graphs"],
                    "difficulty": "beginner",
                    "question_types": ["multiple_choice", "true_false"]
                },
                {
                    "title": "Node Relationships",
                    "concepts": ["connections", "relationships", "traversal"],
                    "difficulty": "intermediate",
                    "question_types": ["fill_in_blank", "code_completion"]
                }
            ],
            "default": [
                {
                    "title": "General Programming Concepts",
                    "concepts": ["variables", "functions", "logic"],
                    "difficulty": "beginner",
                    "question_types": ["multiple_choice", "true_false"]
                }
            ]
        }
        
    async def _update_user_skill_assessment(self, progress_data: Dict[str, Any]):
        """Update user skill assessment based on progress"""
        # Implementation for updating user skill assessment
        pass
        
    async def _analyze_performance_so_far(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance so far for difficulty adaptation"""
        if not responses:
            return {"performance_score": 0.5, "trend": "stable"}
            
        # Calculate performance metrics
        correct_count = sum(1 for r in responses if r.get("is_correct", False))
        total_count = len(responses)
        accuracy = correct_count / total_count if total_count > 0 else 0
        
        # Calculate time efficiency
        avg_time = sum(r.get("time_taken_seconds", 60) for r in responses) / total_count
        
        return {
            "accuracy": accuracy,
            "average_time": avg_time,
            "questions_answered": total_count,
            "performance_score": (accuracy + (1.0 - avg_time/120)) / 2  # Normalized score
        }
        
    async def _determine_difficulty_adjustments(self, performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine difficulty adjustments based on performance"""
        performance_score = performance_analysis.get("performance_score", 0.5)
        
        if performance_score > 0.8:
            adjustment = "increase"
            target_difficulty = "advanced"
        elif performance_score < 0.4:
            adjustment = "decrease"
            target_difficulty = "beginner"
        else:
            adjustment = "maintain"
            target_difficulty = "intermediate"
            
        return {
            "adjustment": adjustment,
            "target_difficulty": target_difficulty,
            "confidence": abs(performance_score - 0.5) * 2  # How confident we are
        }
        
    async def _apply_difficulty_adjustments(self, quiz_id: UUID, adjustments: Dict[str, Any]) -> List[Question]:
        """Apply difficulty adjustments to remaining questions"""
        # Implementation for applying adjustments
        return []
        
    async def _get_quiz_responses(self, quiz_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        """Get quiz responses from database"""
        async with self.database_pool.acquire() as conn:
            responses = await conn.fetch("""
                SELECT * FROM quiz_responses WHERE quiz_id = $1 AND user_id = $2
            """, quiz_id, user_id)
            
        return [dict(row) for row in responses]
        
    async def _calculate_quiz_analytics(self, quiz: Quiz, responses: List[Dict[str, Any]]) -> QuizAnalytics:
        """Calculate comprehensive quiz analytics"""
        correct_answers = sum(1 for r in responses if r.get("is_correct", False))
        total_questions = len(responses)
        
        analytics = QuizAnalytics(
            quiz_id=quiz.quiz_id,
            user_id=quiz.user_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            accuracy_percentage=(correct_answers / total_questions * 100) if total_questions > 0 else 0,
            average_time_per_question=sum(r.get("time_taken_seconds", 60) for r in responses) / total_questions if total_questions > 0 else 0,
            initial_difficulty=quiz.questions[0].difficulty if quiz.questions else DifficultyLevel.INTERMEDIATE,
            final_difficulty=quiz.questions[-1].difficulty if quiz.questions else DifficultyLevel.INTERMEDIATE
        )
        
        return analytics
        
    async def _store_quiz_analytics(self, analytics: QuizAnalytics):
        """Store quiz analytics in database"""
        async with self.database_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO quiz_analytics (
                    quiz_id, user_id, total_questions, correct_answers,
                    accuracy_percentage, average_time_per_question
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                analytics.quiz_id, analytics.user_id, analytics.total_questions,
                analytics.correct_answers, analytics.accuracy_percentage,
                analytics.average_time_per_question
            )
            
    async def _generate_learning_insights(self, analytics: QuizAnalytics) -> List[str]:
        """Generate learning insights from quiz analytics"""
        insights = []
        
        if analytics.accuracy_percentage >= 80:
            insights.append("Excellent performance! You're mastering these concepts well.")
        elif analytics.accuracy_percentage >= 60:
            insights.append("Good progress! Keep practicing to improve further.")
        else:
            insights.append("Consider reviewing the fundamental concepts before continuing.")
            
        if analytics.difficulty_adjustments_made > 0:
            insights.append(f"The quiz adapted {analytics.difficulty_adjustments_made} times based on your performance.")
            
        return insights


# Agent factory function
def create_quiz_generator_agent() -> QuizGeneratorAgent:
    """Create and configure Quiz Generator Agent"""
    return QuizGeneratorAgent()


# Export
__all__ = [
    "QuizGeneratorAgent",
    "Question", 
    "Quiz",
    "QuizResponse",
    "QuizAnalytics",
    "AdaptiveParameters",
    "create_quiz_generator_agent"
]