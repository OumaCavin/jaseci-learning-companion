#!/usr/bin/env python3
"""
Jaseci Learning Companion - Quiz Generator Agent
Agent for generating AI-powered quizzes and assessments

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from database.connection import get_db

logger = logging.getLogger(__name__)

@dataclass
class QuizQuestion:
    """Quiz question data structure"""
    question_id: str
    question_type: str  # multiple_choice, true_false, short_answer, code_analysis
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    difficulty_level: int = 1  # 1-5
    points: int = 1
    code_snippet: Optional[str] = None
    tags: Optional[List[str]] = None

@dataclass
class Quiz:
    """Quiz data structure"""
    quiz_id: str
    title: str
    description: str
    questions: List[QuizQuestion]
    total_points: int
    time_limit: Optional[int] = None  # minutes
    created_by: str
    created_at: datetime
    difficulty_level: int = 1
    topic_area: str = "general"

class QuizGeneratorAgent:
    """Enterprise quiz generation agent"""
    
    def __init__(self, agent_id: str = "quiz_generator_agent"):
        self.agent_id = agent_id
        self.agent_type = "quiz_generator"
        self.capabilities = [
            "quiz_generation", 
            "question_creation", 
            "difficulty_adaptation",
            "assessment_creation",
            "adaptive_testing"
        ]
        self.status = "initializing"
        self.last_heartbeat = datetime.utcnow()
    
    async def initialize(self):
        """Initialize agent"""
        try:
            self.status = "ready"
            self.last_heartbeat = datetime.utcnow()
            logger.info(f"Quiz Generator Agent initialized: {self.agent_id}")
        except Exception as e:
            logger.error(f"Error initializing Quiz Generator Agent: {e}")
            self.status = "error"
    
    async def heartbeat(self):
        """Agent heartbeat"""
        self.last_heartbeat = datetime.utcnow()
        self.status = "active"
    
    async def handle_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quiz generation task"""
        try:
            await self.heartbeat()
            
            task_type = task_data.get("task_type")
            
            if task_type == "generate_quiz":
                return await self._generate_quiz(task_data)
            elif task_type == "generate_assessment":
                return await self._generate_assessment(task_data)
            elif task_type == "adaptive_quiz":
                return await self._generate_adaptive_quiz(task_data)
            elif task_type == "analyze_performance":
                return await self._analyze_performance(task_data)
            else:
                return {"error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"Error handling task in Quiz Generator Agent: {e}")
            return {"error": str(e)}
    
    async def _generate_quiz(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new quiz"""
        try:
            title = task_data.get("title", "Jaseci Quiz")
            topic_area = task_data.get("topic_area", "general")
            difficulty_level = task_data.get("difficulty_level", 2)
            question_count = task_data.get("question_count", 10)
            created_by = task_data.get("created_by", "system")
            time_limit = task_data.get("time_limit")  # minutes
            
            # Generate questions
            questions = await self._generate_questions(topic_area, difficulty_level, question_count)
            
            # Create quiz
            quiz = Quiz(
                quiz_id=f"quiz_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                title=title,
                description=f"A {difficulty_level}-level quiz on {topic_area}",
                questions=questions,
                total_points=sum(q.points for q in questions),
                time_limit=time_limit,
                created_by=created_by,
                created_at=datetime.utcnow(),
                difficulty_level=difficulty_level,
                topic_area=topic_area
            )
            
            # Store in database
            await self._store_quiz(quiz)
            
            result = {
                "status": "quiz_generated",
                "quiz": {
                    "quiz_id": quiz.quiz_id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "question_count": len(quiz.questions),
                    "total_points": quiz.total_points,
                    "time_limit": quiz.time_limit,
                    "difficulty_level": quiz.difficulty_level,
                    "topic_area": quiz.topic_area
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Quiz generated: {quiz.quiz_id} with {len(questions)} questions")
            return result
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return {"error": str(e)}
    
    async def _generate_assessment(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive assessment"""
        try:
            topic_area = task_data.get("topic_area", "comprehensive")
            difficulty_level = task_data.get("difficulty_level", 3)
            assessment_type = task_data.get("assessment_type", "final")  # quiz, midterm, final
            created_by = task_data.get("created_by", "system")
            
            # Generate different types of questions for comprehensive assessment
            questions = []
            
            # Basic concepts
            basic_questions = await self._generate_questions(topic_area, 1, 5)
            questions.extend(basic_questions)
            
            # Intermediate concepts
            intermediate_questions = await self._generate_questions(topic_area, 2, 8)
            questions.extend(intermediate_questions)
            
            # Advanced concepts
            advanced_questions = await self._generate_questions(topic_area, 4, 5)
            questions.extend(advanced_questions)
            
            # Add code analysis questions for technical assessments
            if assessment_type in ["midterm", "final"]:
                code_questions = await self._generate_code_analysis_questions(3)
                questions.extend(code_questions)
            
            # Create assessment
            assessment = Quiz(
                quiz_id=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                title=f"{topic_area.title()} {assessment_type.title()} Assessment",
                description=f"Comprehensive {assessment_type} assessment for {topic_area}",
                questions=questions,
                total_points=sum(q.points for q in questions),
                time_limit=120,  # 2 hours for comprehensive assessment
                created_by=created_by,
                created_at=datetime.utcnow(),
                difficulty_level=difficulty_level,
                topic_area=topic_area
            )
            
            await self._store_quiz(assessment)
            
            result = {
                "status": "assessment_generated",
                "assessment": {
                    "quiz_id": assessment.quiz_id,
                    "title": assessment.title,
                    "description": assessment.description,
                    "question_count": len(assessment.questions),
                    "total_points": assessment.total_points,
                    "time_limit": assessment.time_limit,
                    "assessment_type": assessment_type
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Assessment generated: {assessment.quiz_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating assessment: {e}")
            return {"error": str(e)}
    
    async def _generate_adaptive_quiz(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an adaptive quiz based on user performance"""
        try:
            user_id = task_data.get("user_id")
            topic_area = task_data.get("topic_area", "general")
            created_by = task_data.get("created_by", "system")
            
            if not user_id:
                return {"error": "Missing user_id for adaptive quiz"}
            
            # Get user's performance history
            user_performance = await self._get_user_performance(user_id, topic_area)
            
            # Determine appropriate difficulty
            difficulty_level = self._determine_adaptive_difficulty(user_performance)
            
            # Generate questions based on user's skill level
            question_count = 15  # Standard adaptive quiz length
            questions = await self._generate_adaptive_questions(topic_area, difficulty_level, question_count, user_performance)
            
            adaptive_quiz = Quiz(
                quiz_id=f"adaptive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                title=f"Adaptive {topic_area.title()} Quiz",
                description=f"Personalized quiz based on your performance",
                questions=questions,
                total_points=sum(q.points for q in questions),
                time_limit=30,
                created_by=created_by,
                created_at=datetime.utcnow(),
                difficulty_level=difficulty_level,
                topic_area=topic_area
            )
            
            await self._store_quiz(adaptive_quiz)
            
            result = {
                "status": "adaptive_quiz_generated",
                "adaptive_quiz": {
                    "quiz_id": adaptive_quiz.quiz_id,
                    "title": adaptive_quiz.title,
                    "determined_difficulty": difficulty_level,
                    "question_count": len(adaptive_quiz.questions),
                    "total_points": adaptive_quiz.total_points,
                    "reasoning": f"Based on your performance, you're at level {difficulty_level}"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Adaptive quiz generated for user {user_id}: {adaptive_quiz.quiz_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating adaptive quiz: {e}")
            return {"error": str(e)}
    
    async def _analyze_performance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user quiz performance"""
        try:
            user_id = task_data.get("user_id")
            quiz_id = task_data.get("quiz_id")
            
            if not user_id:
                return {"error": "Missing user_id"}
            
            async with get_db() as conn:
                # Get quiz attempts
                attempts = await conn.fetch("""
                    SELECT qa.*, q.title, q.difficulty_level, q.topic_area
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE qa.user_id = $1
                    ORDER BY qa.attempted_at DESC
                """, user_id)
                
                if not attempts:
                    return {"error": "No quiz attempts found for user"}
                
                # Calculate performance metrics
                total_attempts = len(attempts)
                avg_score = sum(a["score"] for a in attempts) / total_attempts
                best_score = max(a["score"] for a in attempts)
                recent_attempts = [a for a in attempts if a["attempted_at"] >= datetime.utcnow() - timedelta(days=30)]
                
                # Analyze by topic
                topic_performance = {}
                for attempt in attempts:
                    topic = attempt["topic_area"]
                    if topic not in topic_performance:
                        topic_performance[topic] = []
                    topic_performance[topic].append(attempt["score"])
                
                topic_stats = {}
                for topic, scores in topic_performance.items():
                    topic_stats[topic] = {
                        "attempts": len(scores),
                        "avg_score": round(sum(scores) / len(scores), 2),
                        "best_score": max(scores)
                    }
                
                # Performance trends
                trend_analysis = await self._analyze_performance_trends(user_id)
                
                result = {
                    "status": "performance_analyzed",
                    "user_id": user_id,
                    "overall_stats": {
                        "total_attempts": total_attempts,
                        "avg_score": round(avg_score, 2),
                        "best_score": best_score,
                        "recent_activity": len(recent_attempts)
                    },
                    "topic_performance": topic_stats,
                    "trends": trend_analysis,
                    "recommendations": await self._generate_performance_recommendations(user_id, topic_stats),
                    "analyzed_at": datetime.utcnow().isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {"error": str(e)}
    
    async def _generate_questions(self, topic_area: str, difficulty_level: int, count: int) -> List[QuizQuestion]:
        """Generate questions for a quiz"""
        questions = []
        
        # Question templates by topic and difficulty
        question_templates = self._get_question_templates(topic_area, difficulty_level)
        
        for i in range(count):
            template = random.choice(question_templates)
            question = await self._create_question_from_template(template, i + 1)
            questions.append(question)
        
        return questions
    
    async def _generate_adaptive_questions(self, topic_area: str, difficulty_level: int, count: int, user_performance: Dict) -> List[QuizQuestion]:
        """Generate adaptive questions based on user performance"""
        questions = []
        
        # Adjust difficulty based on performance
        base_difficulty = difficulty_level
        if user_performance.get("avg_score", 0) > 80:
            # Increase difficulty for high performers
            difficulty_level = min(5, difficulty_level + 1)
        elif user_performance.get("avg_score", 0) < 60:
            # Decrease difficulty for low performers
            difficulty_level = max(1, difficulty_level - 1)
        
        # Generate questions with adaptive difficulty
        question_templates = self._get_question_templates(topic_area, difficulty_level)
        
        for i in range(count):
            template = random.choice(question_templates)
            question = await self._create_question_from_template(template, i + 1)
            questions.append(question)
        
        return questions
    
    async def _generate_code_analysis_questions(self, count: int) -> List[QuizQuestion]:
        """Generate code analysis questions"""
        questions = []
        
        code_scenarios = [
            {
                "code": "walker my_walker {\n  has input_text;\n  has output_result;\n  \n  walk {\n    output_result = input_text.upper();\n  }\n}",
                "question": "What will be the output of this Jaseci walker?",
                "correct_answer": "Converts input to uppercase",
                "explanation": "The walker applies the .upper() method to convert text to uppercase."
            },
            {
                "code": "node user {\n  has name;\n  has age;\n  has email;\n}\n\nedge friend;\n\ngraph social_network {\n  has anchor users;\n}",
                "question": "What type of relationship does the 'friend' edge represent?",
                "correct_answer": "Many-to-many relationship between users",
                "explanation": "The friend edge creates a many-to-many relationship allowing users to connect with multiple friends."
            }
        ]
        
        for i in range(count):
            scenario = random.choice(code_scenarios)
            question = QuizQuestion(
                question_id=f"code_q_{i+1}",
                question_type="code_analysis",
                question_text=scenario["question"],
                correct_answer=scenario["correct_answer"],
                explanation=scenario["explanation"],
                code_snippet=scenario["code"],
                difficulty_level=3,
                points=2,
                tags=["code_analysis", "jaseci"]
            )
            questions.append(question)
        
        return questions
    
    def _get_question_templates(self, topic_area: str, difficulty_level: int) -> List[Dict[str, Any]]:
        """Get question templates based on topic and difficulty"""
        templates = []
        
        # Basic Jaseci concepts
        basic_templates = [
            {
                "type": "multiple_choice",
                "question": "What is the primary purpose of Jaseci?",
                "options": ["Web development", "Graph-based AI programming", "Database management", "Mobile app development"],
                "correct_answer": 1,
                "explanation": "Jaseci is designed for graph-based AI programming and application development."
            },
            {
                "type": "multiple_choice",
                "question": "Which of these is a valid Jaseci node type?",
                "options": ["walker", "graph", "edge", "all of the above"],
                "correct_answer": 3,
                "explanation": "Jaseci supports walker, graph, node, and edge types for building AI applications."
            },
            {
                "type": "true_false",
                "question": "Jaseci walkers can only be executed on a single node.",
                "correct_answer": False,
                "explanation": "Jaseci walkers can traverse across multiple nodes in a graph."
            }
        ]
        
        # Intermediate concepts
        intermediate_templates = [
            {
                "type": "multiple_choice",
                "question": "What does the 'take' statement do in Jaseci?",
                "options": [
                    "Removes a node from the graph",
                    "Selects specific nodes for processing",
                    "Creates a new edge",
                    "Updates node properties"
                ],
                "correct_answer": 1,
                "explanation": "The 'take' statement is used to select or filter nodes for processing in a walker."
            },
            {
                "type": "short_answer",
                "question": "Explain the difference between 'can' and 'has' in Jaseci node definitions.",
                "correct_answer": "can defines methods, has defines properties",
                "explanation": "'can' is used to define methods/behaviors, while 'has' defines properties/data attributes."
            }
        ]
        
        # Advanced concepts
        advanced_templates = [
            {
                "type": "multiple_choice",
                "question": "Which pattern is best for implementing state machines in Jaseci?",
                "options": [
                    "Multiple walkers with shared state",
                    "Single walker with conditional logic",
                    "Graph structure with edge-based state",
                    "External state management"
                ],
                "correct_answer": 2,
                "explanation": "Graph structure with edge-based state allows for clean state machine implementation."
            }
        ]
        
        # Select templates based on difficulty
        if difficulty_level <= 2:
            templates = basic_templates + intermediate_templates[:2]
        elif difficulty_level <= 3:
            templates = intermediate_templates + advanced_templates[:1]
        else:
            templates = intermediate_templates + advanced_templates
        
        return templates
    
    async def _create_question_from_template(self, template: Dict[str, Any], question_num: int) -> QuizQuestion:
        """Create a question from a template"""
        question_id = f"q_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{question_num}"
        
        return QuizQuestion(
            question_id=question_id,
            question_type=template["type"],
            question_text=template["question"],
            options=template.get("options"),
            correct_answer=template.get("correct_answer"),
            explanation=template.get("explanation"),
            difficulty_level=template.get("difficulty_level", 2),
            points=template.get("points", 1),
            tags=template.get("tags", ["jaseci"])
        )
    
    async def _get_user_performance(self, user_id: str, topic_area: str) -> Dict[str, Any]:
        """Get user's performance history"""
        try:
            async with get_db() as conn:
                performance = await conn.fetchrow("""
                    SELECT 
                        AVG(score) as avg_score,
                        COUNT(*) as total_attempts,
                        MAX(score) as best_score,
                        MIN(score) as worst_score
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE qa.user_id = $1 AND q.topic_area = $2
                """, user_id, topic_area)
                
                return dict(performance) if performance else {"avg_score": 0, "total_attempts": 0}
                
        except Exception as e:
            logger.error(f"Error getting user performance: {e}")
            return {"avg_score": 0, "total_attempts": 0}
    
    def _determine_adaptive_difficulty(self, user_performance: Dict[str, Any]) -> int:
        """Determine appropriate difficulty based on user performance"""
        avg_score = user_performance.get("avg_score", 0)
        total_attempts = user_performance.get("total_attempts", 0)
        
        # Adjust difficulty based on performance
        if total_attempts == 0:
            return 2  # Start with medium difficulty for new users
        
        if avg_score >= 90:
            return 5  # Very high performance
        elif avg_score >= 80:
            return 4  # High performance
        elif avg_score >= 70:
            return 3  # Good performance
        elif avg_score >= 60:
            return 2  # Average performance
        else:
            return 1  # Needs improvement
    
    async def _store_quiz(self, quiz: Quiz):
        """Store quiz in database"""
        try:
            async with get_db() as conn:
                # Convert quiz to serializable format
                quiz_data = {
                    "quiz_id": quiz.quiz_id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "questions": [self._question_to_dict(q) for q in quiz.questions],
                    "total_points": quiz.total_points,
                    "time_limit": quiz.time_limit,
                    "created_by": quiz.created_by,
                    "difficulty_level": quiz.difficulty_level,
                    "topic_area": quiz.topic_area,
                    "created_at": quiz.created_at
                }
                
                await conn.execute("""
                    INSERT INTO quizzes (
                        quiz_id, title, description, questions, total_points,
                        time_limit, created_by, difficulty_level, topic_area, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (quiz_id)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        questions = EXCLUDED.questions,
                        total_points = EXCLUDED.total_points,
                        time_limit = EXCLUDED.time_limit,
                        difficulty_level = EXCLUDED.difficulty_level,
                        topic_area = EXCLUDED.topic_area
                """, quiz_data["quiz_id"], quiz_data["title"], quiz_data["description"],
                    json.dumps(quiz_data["questions"]), quiz_data["total_points"],
                    quiz_data["time_limit"], quiz_data["created_by"],
                    quiz_data["difficulty_level"], quiz_data["topic_area"],
                    quiz_data["created_at"])
                    
        except Exception as e:
            logger.error(f"Error storing quiz: {e}")
    
    def _question_to_dict(self, question: QuizQuestion) -> Dict[str, Any]:
        """Convert question to dictionary"""
        return {
            "question_id": question.question_id,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "difficulty_level": question.difficulty_level,
            "points": question.points,
            "code_snippet": question.code_snippet,
            "tags": question.tags
        }
    
    async def _analyze_performance_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze user performance trends"""
        try:
            async with get_db() as conn:
                # Get recent performance data
                recent_performance = await conn.fetch("""
                    SELECT 
                        DATE(attempted_at) as date,
                        AVG(score) as avg_score,
                        COUNT(*) as attempts
                    FROM quiz_attempts
                    WHERE user_id = $1 AND attempted_at >= $2
                    GROUP BY DATE(attempted_at)
                    ORDER BY date
                """, user_id, datetime.utcnow() - timedelta(days=30))
                
                if len(recent_performance) < 2:
                    return {"trend": "insufficient_data", "message": "Need more data to determine trends"}
                
                scores = [p["avg_score"] for p in recent_performance]
                
                # Simple trend analysis
                if len(scores) >= 3:
                    if scores[-1] > scores[-2] > scores[-3]:
                        trend = "improving"
                    elif scores[-1] < scores[-2] < scores[-3]:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
                
                return {
                    "trend": trend,
                    "recent_scores": scores,
                    "improvement_rate": round((scores[-1] - scores[0]) / len(scores), 2) if scores else 0
                }
                
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {"trend": "error", "message": str(e)}
    
    async def _generate_performance_recommendations(self, user_id: str, topic_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance-based recommendations"""
        recommendations = []
        
        # Analyze weak areas
        for topic, stats in topic_stats.items():
            if stats["avg_score"] < 70:
                recommendations.append({
                    "type": "improvement",
                    "topic": topic,
                    "message": f"Focus on {topic} - current average is {stats['avg_score']}%",
                    "priority": "high"
                })
            elif stats["avg_score"] > 90:
                recommendations.append({
                    "type": "mastery",
                    "topic": topic,
                    "message": f"Excellent performance in {topic}! Consider advanced topics.",
                    "priority": "low"
                })
        
        # General recommendations
        if not recommendations:
            recommendations.append({
                "type": "encouragement",
                "message": "Keep up the good work! Consider challenging yourself with harder questions.",
                "priority": "medium"
            })
        
        return recommendations
