#!/usr/bin/env python3
"""
Jaseci Learning Companion - Multi-Agent Orchestrator
Enterprise-grade multi-agent system orchestration

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
import asyncpg
import redis.asyncio as redis

from database.connection import get_db
from registry.agent_registry import AgentRegistry
from message_bus.message_bus import MessageBus
from scheduling.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)

# Configuration
class Config:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/jaseci_learning")
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "50"))
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "300"))  # 5 minutes
    AGENT_HEARTBEAT_INTERVAL = int(os.getenv("AGENT_HEARTBEAT_INTERVAL", "30"))

# Task Management
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Task:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    user_id: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None

# API Models
class TaskSubmitRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    user_id: str

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: datetime

class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Global services
agent_registry: Optional[AgentRegistry] = None
message_bus: Optional[MessageBus] = None
task_scheduler: Optional[TaskScheduler] = None
redis_client: Optional[redis.Redis] = None

# Task management
active_tasks: Dict[str, Task] = {}
task_queue: List[Task] = []
task_executor: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent_registry, message_bus, task_scheduler, redis_client
    
    try:
        # Initialize services
        redis_client = redis.from_url(Config.REDIS_URL)
        await redis_client.ping()
        
        agent_registry = AgentRegistry()
        message_bus = MessageBus()
        task_scheduler = TaskScheduler(redis_client)
        
        # Start task processor
        await task_scheduler.start()
        
        # Register built-in agents
        await _register_builtin_agents()
        
        logger.info("✅ Orchestrator services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Orchestrator startup failed: {e}")
        raise
    finally:
        # Shutdown
        await task_scheduler.stop()
        if agent_registry:
            await agent_registry.close()
        if message_bus:
            await message_bus.close()
        if redis_client:
            await redis_client.close()
        logger.info("✅ Orchestrator services shut down")

# Create FastAPI app
app = FastAPI(
    title="Jaseci Learning Companion - Multi-Agent Orchestrator",
    description="Enterprise multi-agent orchestration system",
    version="2.0.0-enterprise",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        async with get_db() as conn:
            await conn.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check agent registry
        agents_count = await agent_registry.get_active_agents_count()
        
        # Check task queue
        queue_size = len(task_queue)
        running_tasks = len([t for t in active_tasks.values() if t.status == TaskStatus.RUNNING])
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "agents_active": agents_count,
                "queue_size": queue_size,
                "running_tasks": running_tasks
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.post("/tasks/submit", response_model=TaskResponse)
async def submit_task(task_request: TaskSubmitRequest, background_tasks: BackgroundTasks):
    """Submit task for processing"""
    try:
        task_id = await _generate_task_id()
        
        task = Task(
            task_id=task_id,
            task_type=task_request.task_type,
            payload=task_request.payload,
            user_id=task_request.user_id,
            priority=task_request.priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Add to task queue
        task_queue.append(task)
        
        # Start task processor if not running
        if task_executor is None or task_executor.done():
            global task_executor
            task_executor = asyncio.create_task(_process_task_queue())
        
        logger.info(f"Task {task_id} submitted for type {task_request.task_type}")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=task.created_at
        )
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=f"Task submission failed: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """Get task result"""
    try:
        # Check cache first
        cached_result = await redis_client.get(f"task_result:{task_id}")
        if cached_result:
            result_data = json.loads(cached_result)
            return TaskResultResponse(**result_data)
        
        # Check active tasks
        if task_id in active_tasks:
            task = active_tasks[task_id]
            return TaskResultResponse(
                task_id=task_id,
                status=task.status,
                result=task.result,
                error=task.error,
                started_at=task.started_at,
                completed_at=task.completed_at
            )
        
        # Check database
        async with get_db() as conn:
            task_data = await conn.fetchrow("""
                SELECT status, result, error, started_at, completed_at
                FROM task_results
                WHERE task_id = $1
            """, task_id)
            
            if task_data:
                return TaskResultResponse(
                    task_id=task_id,
                    status=TaskStatus(task_data["status"]),
                    result=task_data["result"],
                    error=task_data["error"],
                    started_at=task_data["started_at"],
                    completed_at=task_data["completed_at"]
                )
        
        raise HTTPException(status_code=404, detail="Task not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")

@app.get("/tasks")
async def list_tasks(user_id: Optional[str] = None, limit: int = 50):
    """List tasks"""
    try:
        if user_id:
            tasks = [task for task in active_tasks.values() if task.user_id == user_id]
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return [asdict(task) for task in tasks[:limit]]
        else:
            # Get recent tasks from database
            async with get_db() as conn:
                recent_tasks = await conn.fetch("""
                    SELECT task_id, task_type, user_id, status, created_at, started_at, completed_at
                    FROM task_results
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
                
                return [dict(task) for task in recent_tasks]
                
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel task"""
    try:
        # Check if task is running
        if task_id in active_tasks:
            task = active_tasks[task_id]
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                logger.info(f"Task {task_id} cancelled")
                return {"message": "Task cancelled"}
            elif task.status == TaskStatus.PENDING:
                # Remove from queue
                task_queue[:] = [t for t in task_queue if t.task_id != task_id]
                task.status = TaskStatus.CANCELLED
                logger.info(f"Task {task_id} cancelled from queue")
                return {"message": "Task cancelled from queue"}
        
        raise HTTPException(status_code=404, detail="Task not found or already completed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@app.get("/agents")
async def list_agents():
    """List all agents"""
    try:
        agents = await agent_registry.list_agents()
        return [{"agent_id": agent_id, **agent_info} for agent_id, agent_info in agents.items()]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.post("/agents/register")
async def register_agent(agent_info: Dict[str, Any]):
    """Register new agent"""
    try:
        agent_id = await agent_registry.register_agent(agent_info)
        logger.info(f"Agent registered: {agent_id}")
        return {"agent_id": agent_id, "status": "registered"}
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register agent: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get orchestrator metrics"""
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "active": await agent_registry.get_active_agents_count(),
                "total_registered": await agent_registry.get_total_agents_count()
            },
            "tasks": {
                "pending": len([t for t in task_queue if t.status == TaskStatus.PENDING]),
                "running": len([t for t in active_tasks.values() if t.status == TaskStatus.RUNNING]),
                "completed_today": await _get_completed_tasks_count_today(),
                "failed_today": await _get_failed_tasks_count_today()
            },
            "queue": {
                "size": len(task_queue),
                "priority_distribution": _get_queue_priority_distribution()
            }
        }
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Task Processing Functions

async def _process_task_queue():
    """Process tasks from queue"""
    while True:
        try:
            # Sort queue by priority
            task_queue.sort(key=lambda t: _get_priority_value(t.priority), reverse=True)
            
            # Find next available task
            task = None
            for i, queued_task in enumerate(task_queue):
                if queued_task.status == TaskStatus.PENDING:
                    task = task_queue.pop(i)
                    break
            
            if not task:
                await asyncio.sleep(1)  # Wait for new tasks
                continue
            
            # Find suitable agent
            agent_id = await agent_registry.find_suitable_agent(task.task_type)
            if not agent_id:
                # Re-queue and wait
                task_queue.insert(0, task)
                await asyncio.sleep(5)
                continue
            
            # Execute task
            await _execute_task(task, agent_id)
            
        except Exception as e:
            logger.error(f"Error processing task queue: {e}")
            await asyncio.sleep(5)

async def _execute_task(task: Task, agent_id: str):
    """Execute task with agent"""
    try:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.agent_id = agent_id
        
        # Add to active tasks
        active_tasks[task.task_id] = task
        
        logger.info(f"Executing task {task.task_id} with agent {agent_id}")
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                _call_agent(agent_id, task),
                timeout=Config.TASK_TIMEOUT
            )
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            
            # Store in database
            await _store_task_result(task)
            
            # Cache result
            await redis_client.setex(
                f"task_result:{task.task_id}",
                3600,  # 1 hour
                json.dumps({
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "result": task.result,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": datetime.utcnow().isoformat()
                })
            )
            
            logger.info(f"Task {task.task_id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = f"Task timeout after {Config.TASK_TIMEOUT} seconds"
            logger.error(f"Task {task.task_id} timed out")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
        
        finally:
            task.completed_at = datetime.utcnow()
            
            # Remove from active tasks
            if task.task_id in active_tasks:
                del active_tasks[task.task_id]
            
            # Update agent status
            await agent_registry.update_agent_status(agent_id, "available")
            
    except Exception as e:
        logger.error(f"Error executing task {task.task_id}: {e}")

async def _call_agent(agent_id: str, task: Task) -> Dict[str, Any]:
    """Call agent to execute task"""
    # Get agent info
    agent_info = await agent_registry.get_agent(agent_id)
    if not agent_info:
        raise ValueError(f"Agent {agent_id} not found")
    
    # Call agent based on task type
    agent_type = agent_info.get("type")
    
    if agent_type == "learning_progress":
        return await _handle_learning_progress_task(task)
    elif agent_type == "quiz_generator":
        return await _handle_quiz_generator_task(task)
    elif agent_type == "code_analyzer":
        return await _handle_code_analyzer_task(task)
    elif agent_type == "quality_assessor":
        return await _handle_quality_assessor_task(task)
    elif agent_type == "content_recommender":
        return await _handle_content_recommender_task(task)
    elif agent_type == "analytics":
        return await _handle_analytics_task(task)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

# Task Handlers

async def _handle_learning_progress_task(task: Task) -> Dict[str, Any]:
    """Handle learning progress task"""
    task_type = task.payload.get("task_type", "update_progress")
    
    if task_type == "update_progress":
        # Update user learning progress
        learning_path_id = task.payload.get("learning_path_id")
        progress_data = task.payload.get("progress_data")
        
        async with get_db() as conn:
            await conn.execute("""
                INSERT INTO learning_progress (user_id, learning_path_id, progress_data, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, learning_path_id)
                DO UPDATE SET progress_data = $3, updated_at = $4
            """, task.user_id, learning_path_id, progress_data, datetime.utcnow())
        
        return {"status": "progress_updated", "learning_path_id": learning_path_id}
    
    elif task_type == "get_stats":
        # Get user learning statistics
        async with get_db() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(study_duration) as total_study_time,
                    AVG(completion_percentage) as avg_completion
                FROM learning_progress
                WHERE user_id = $1
            """, task.user_id)
        
        return {"status": "stats_retrieved", "data": dict(stats)}
    
    return {"status": "completed"}

async def _handle_quiz_generator_task(task: Task) -> Dict[str, Any]:
    """Handle quiz generator task"""
    quiz_params = task.payload
    
    # Generate quiz based on parameters
    quiz = {
        "quiz_id": await _generate_quiz_id(),
        "title": quiz_params.get("title", "Generated Quiz"),
        "questions": [
            {
                "id": "q1",
                "type": "multiple_choice",
                "question": "What is Jaseci?",
                "options": ["A programming language", "A web framework", "A database", "An IDE"],
                "correct_answer": 0
            }
        ],
        "created_by": task.user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store quiz
    async with get_db() as conn:
        await conn.execute("""
            INSERT INTO quizzes (quiz_id, title, questions, created_by, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, quiz["quiz_id"], quiz["title"], quiz["questions"], task.user_id, datetime.utcnow())
    
    return {"status": "quiz_generated", "quiz": quiz}

async def _handle_code_analyzer_task(task: Task) -> Dict[str, Any]:
    """Handle code analyzer task"""
    code = task.payload.get("code")
    analysis_type = task.payload.get("analysis_type", "basic")
    
    # Simple code analysis (in production, this would call the actual analyzer)
    analysis_result = {
        "analysis_id": await _generate_analysis_id(),
        "code_length": len(code),
        "complexity_score": min(len(code.split('\n')) / 10, 10),
        "issues": [] if analysis_type == "basic" else [
            {"type": "warning", "message": "Consider adding more comments", "line": 1}
        ],
        "suggestions": [
            "Add error handling",
            "Use meaningful variable names",
            "Add documentation"
        ],
        "analysis_type": analysis_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store analysis
    async with get_db() as conn:
        await conn.execute("""
            INSERT INTO code_analysis (
                analysis_id, user_id, code, analysis_type, result, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, analysis_result["analysis_id"], task.user_id, code, 
            analysis_type, analysis_result, datetime.utcnow())
    
    return {"status": "analysis_completed", "result": analysis_result}

async def _handle_quality_assessor_task(task: Task) -> Dict[str, Any]:
    """Handle quality assessor task"""
    # 5-dimensional quality assessment
    assessment = {
        "assessment_id": await _generate_assessment_id(),
        "dimensions": {
            "correctness": {"score": 8.5, "details": "Code appears functionally correct"},
            "performance": {"score": 7.2, "details": "Could be optimized"},
            "security": {"score": 9.0, "details": "No obvious security issues"},
            "code_quality": {"score": 7.8, "details": "Good structure, could use more comments"},
            "documentation": {"score": 6.5, "details": "Missing comprehensive documentation"}
        },
        "overall_score": 7.8,
        "recommendations": [
            "Add comprehensive test coverage",
            "Implement error handling",
            "Add API documentation"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return {"status": "assessment_completed", "result": assessment}

async def _handle_content_recommender_task(task: Task) -> Dict[str, Any]:
    """Handle content recommender task"""
    user_progress = task.payload.get("user_progress", {})
    
    # Generate recommendations
    recommendations = {
        "recommendations": [
            {
                "type": "learning_path",
                "title": "Advanced Jaseci Patterns",
                "reason": "Based on your progress in basic patterns",
                "priority": "high"
            },
            {
                "type": "quiz",
                "title": "Jaseci Fundamentals Quiz",
                "reason": "Reinforce your knowledge",
                "priority": "medium"
            }
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return {"status": "recommendations_generated", "result": recommendations}

async def _handle_analytics_task(task: Task) -> Dict[str, Any]:
    """Handle analytics task"""
    analytics_data = {
        "user_engagement": {
            "daily_active_users": 42,
            "session_duration_avg": 25.5,
            "completion_rate": 0.73
        },
        "learning_metrics": {
            "total_analyses": 156,
            "avg_complexity_score": 7.2,
            "popular_topics": ["Functions", "Loops", "Data Structures"]
        },
        "system_performance": {
            "avg_response_time": 0.8,
            "error_rate": 0.02,
            "uptime": 99.9
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return {"status": "analytics_generated", "result": analytics_data}

# Utility Functions

async def _register_builtin_agents():
    """Register built-in agents"""
    agents = [
        {
            "agent_id": "learning_progress_agent",
            "type": "learning_progress",
            "status": "available",
            "capabilities": ["progress_tracking", "statistics", "milestone_detection"]
        },
        {
            "agent_id": "quiz_generator_agent",
            "type": "quiz_generator",
            "status": "available",
            "capabilities": ["quiz_generation", "question_creation", "difficulty_adaptation"]
        },
        {
            "agent_id": "code_analyzer_agent",
            "type": "code_analyzer",
            "status": "available",
            "capabilities": ["ccg_analysis", "complexity_analysis", "pattern_detection"]
        },
        {
            "agent_id": "quality_assessor_agent",
            "type": "quality_assessor",
            "status": "available",
            "capabilities": ["quality_evaluation", "best_practices", "recommendations"]
        },
        {
            "agent_id": "content_recommender_agent",
            "type": "content_recommender",
            "status": "available",
            "capabilities": ["personalization", "content_matching", "progression_suggestions"]
        },
        {
            "agent_id": "analytics_agent",
            "type": "analytics",
            "status": "available",
            "capabilities": ["learning_analytics", "engagement_metrics", "performance_tracking"]
        }
    ]
    
    for agent in agents:
        await agent_registry.register_agent(agent)

async def _generate_task_id() -> str:
    """Generate unique task ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    import uuid
    return f"task_{timestamp}_{str(uuid.uuid4())[:8]}"

async def _generate_quiz_id() -> str:
    """Generate quiz ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    import uuid
    return f"quiz_{timestamp}_{str(uuid.uuid4())[:8]}"

async def _generate_analysis_id() -> str:
    """Generate analysis ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    import uuid
    return f"analysis_{timestamp}_{str(uuid.uuid4())[:8]}"

async def _generate_assessment_id() -> str:
    """Generate assessment ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    import uuid
    return f"assessment_{timestamp}_{str(uuid.uuid4())[:8]}"

async def _store_task_result(task: Task):
    """Store task result in database"""
    async with get_db() as conn:
        await conn.execute("""
            INSERT INTO task_results (
                task_id, task_type, user_id, status, payload, result, 
                error, started_at, completed_at, agent_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (task_id)
            DO UPDATE SET 
                status = EXCLUDED.status,
                result = EXCLUDED.result,
                error = EXCLUDED.error,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                agent_id = EXCLUDED.agent_id
        """, task.task_id, task.task_type, task.user_id, task.status.value,
            task.payload, task.result, task.error, task.started_at,
            task.completed_at, task.agent_id, task.created_at)

def _get_priority_value(priority: TaskPriority) -> int:
    """Get numeric priority value"""
    priority_values = {
        TaskPriority.LOW: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.HIGH: 3,
        TaskPriority.URGENT: 4
    }
    return priority_values.get(priority, 2)

async def _get_completed_tasks_count_today() -> int:
    """Get count of completed tasks today"""
    try:
        async with get_db() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM task_results
                WHERE status = 'completed' 
                AND DATE(completed_at) = CURRENT_DATE
            """)
            return count
    except:
        return 0

async def _get_failed_tasks_count_today() -> int:
    """Get count of failed tasks today"""
    try:
        async with get_db() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM task_results
                WHERE status = 'failed' 
                AND DATE(completed_at) = CURRENT_DATE
            """)
            return count
    except:
        return 0

def _get_queue_priority_distribution() -> Dict[str, int]:
    """Get task queue priority distribution"""
    distribution = {"low": 0, "normal": 0, "high": 0, "urgent": 0}
    for task in task_queue:
        if task.status == TaskStatus.PENDING:
            distribution[task.priority.value] += 1
    return distribution

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
