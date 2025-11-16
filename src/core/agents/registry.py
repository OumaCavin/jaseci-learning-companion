"""
Agent Registry and Orchestration Engine
Multi-Agent System Core Component

This module implements the central registry and orchestration system for managing
the 6 specialized agents in the Jaseci Learning Companion system.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set
from uuid import UUID, uuid4
import json
import time
from datetime import datetime, timezone

import nats
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import redis.asyncio as redis
from contextlib import asynccontextmanager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Enumeration of available agent types"""
    LEARNING_PROGRESS = "learning_progress"
    QUIZ_GENERATOR = "quiz_generator"
    CODE_ANALYZER = "code_analyzer"
    QUALITY_ASSESSOR = "quality_assessor"
    CONTENT_RECOMMENDER = "content_recommender"
    ANALYTICS = "analytics"


class AgentStatus(Enum):
    """Agent operational status"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    OFFLINE = "offline"
    SHUTTING_DOWN = "shutting_down"


class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMetadata:
    """Metadata for agent registration"""
    agent_id: UUID
    agent_type: AgentType
    name: str
    version: str
    capabilities: Set[str]
    max_concurrent_tasks: int = 5
    current_load: int = 0
    status: AgentStatus = AgentStatus.REGISTERED
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: Optional[datetime] = None
    health_check_endpoint: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    """Represents a task assigned to an agent"""
    task_id: UUID
    agent_id: UUID
    task_type: str
    priority: Priority
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_id: UUID, agent_type: AgentType, name: str, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.version = version
        self.status = AgentStatus.INITIALIZING
        self.capabilities: Set[str] = set()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent and register capabilities"""
        pass
        
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a specific task"""
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status"""
        pass
        
    async def start(self):
        """Start the agent's main processing loop"""
        self.running = True
        self.status = AgentStatus.ACTIVE
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process the task
                self.status = AgentStatus.BUSY
                result = await self.process_task(task)
                
                # Mark task as complete
                self.task_queue.task_done()
                
                # Return to idle state
                self.status = AgentStatus.IDLE
                
                # Emit task completion event
                await self._emit_task_completion(task, result)
                
            except asyncio.TimeoutError:
                # No tasks available, continue loop
                continue
            except Exception as e:
                logger.error(f"Agent {self.name} error: {str(e)}")
                self.status = AgentStatus.ERROR
                await asyncio.sleep(5)  # Wait before retrying
                
    async def stop(self):
        """Stop the agent gracefully"""
        self.running = False
        self.status = AgentStatus.SHUTTING_DOWN
        
    async def _emit_task_completion(self, task: AgentTask, result: Dict[str, Any]):
        """Emit task completion event to the message bus"""
        # This will be implemented when we set up the message bus
        pass
        
    async def register_capability(self, capability: str):
        """Register a new capability"""
        self.capabilities.add(capability)
        logger.info(f"Agent {self.name} registered capability: {capability}")


class AgentRegistry:
    """Central registry for managing all agents"""
    
    def __init__(self, redis_client: redis.Redis, nats_client: nats.NATS):
        self.agents: Dict[UUID, AgentMetadata] = {}
        self.redis = redis_client
        self.nats = nats_client
        self._lock = asyncio.Lock()
        
    async def register_agent(self, metadata: AgentMetadata) -> bool:
        """Register a new agent in the registry"""
        async with self._lock:
            try:
                # Store in memory
                self.agents[metadata.agent_id] = metadata
                
                # Store in Redis for persistence
                agent_data = {
                    "agent_id": str(metadata.agent_id),
                    "agent_type": metadata.agent_type.value,
                    "name": metadata.name,
                    "version": metadata.version,
                    "capabilities": list(metadata.capabilities),
                    "max_concurrent_tasks": metadata.max_concurrent_tasks,
                    "current_load": metadata.current_load,
                    "status": metadata.status.value,
                    "registered_at": metadata.registered_at.isoformat(),
                    "config": metadata.config
                }
                
                await self.redis.hset(
                    "agent_registry",
                    str(metadata.agent_id),
                    json.dumps(agent_data, default=str)
                )
                
                # Emit registration event
                await self._emit_registry_event("agent_registered", agent_data)
                
                logger.info(f"Agent {metadata.name} ({metadata.agent_id}) registered successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register agent {metadata.name}: {str(e)}")
                return False
                
    async def unregister_agent(self, agent_id: UUID) -> bool:
        """Remove agent from registry"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    agent_name = self.agents[agent_id].name
                    
                    # Remove from memory
                    del self.agents[agent_id]
                    
                    # Remove from Redis
                    await self.redis.hdel("agent_registry", str(agent_id))
                    
                    # Emit unregistration event
                    await self._emit_registry_event("agent_unregistered", {
                        "agent_id": str(agent_id),
                        "name": agent_name
                    })
                    
                    logger.info(f"Agent {agent_name} ({agent_id}) unregistered")
                    return True
                    
                return False
                
            except Exception as e:
                logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
                return False
                
    async def get_agent(self, agent_id: UUID) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        return self.agents.get(agent_id)
        
    async def find_agents_by_type(self, agent_type: AgentType) -> List[AgentMetadata]:
        """Find all agents of a specific type"""
        return [agent for agent in self.agents.values() 
                if agent.agent_type == agent_type]
        
    async def find_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Find all agents that support a specific capability"""
        return [agent for agent in self.agents.values() 
                if capability in agent.capabilities]
        
    async def get_available_agents(self, agent_type: AgentType) -> List[AgentMetadata]:
        """Get all available agents of a specific type"""
        available = []
        for agent in self.agents.values():
            if (agent.agent_type == agent_type and 
                agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE] and
                agent.current_load < agent.max_concurrent_tasks):
                available.append(agent)
                
        # Sort by load (least loaded first)
        available.sort(key=lambda x: x.current_load)
        return available
        
    async def update_agent_status(self, agent_id: UUID, status: AgentStatus, load: Optional[int] = None):
        """Update agent status and load"""
        async with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.status = status
                agent.last_heartbeat = datetime.now(timezone.utc)
                
                if load is not None:
                    agent.current_load = load
                    
                # Update in Redis
                await self.redis.hset(
                    "agent_registry",
                    str(agent_id),
                    json.dumps({
                        "status": status.value,
                        "current_load": agent.current_load,
                        "last_heartbeat": agent.last_heartbeat.isoformat()
                    }, default=str)
                )
                
    async def _emit_registry_event(self, event_type: str, data: Dict[str, Any]):
        """Emit registry event to NATS"""
        try:
            message = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            
            await self.nats.publish(
                f"registry.events.{event_type}",
                json.dumps(message).encode()
            )
            
        except Exception as e:
            logger.error(f"Failed to emit registry event: {str(e)}")


class TaskAssignmentStrategy(Protocol):
    """Protocol for task assignment strategies"""
    
    async def select_agent(self, agents: List[AgentMetadata], task: AgentTask) -> Optional[AgentMetadata]:
        """Select the best agent for a task"""
        ...


class LoadBalancedStrategy:
    """Load-balanced task assignment strategy"""
    
    async def select_agent(self, agents: List[AgentMetadata], task: AgentTask) -> Optional[AgentMetadata]:
        """Select agent with lowest load"""
        if not agents:
            return None
            
        # Sort by current load (ascending)
        agents.sort(key=lambda x: x.current_load)
        
        # Select agent with lowest load
        selected = agents[0]
        
        # Increment load
        selected.current_load += 1
        
        return selected


class PriorityBasedStrategy:
    """Priority-based task assignment strategy"""
    
    async def select_agent(self, agents: List[AgentMetadata], task: AgentTask) -> Optional[AgentMetadata]:
        """Select agent based on priority and capability"""
        if not agents:
            return None
            
        # Filter agents that can handle the task type
        capable_agents = [agent for agent in agents 
                         if self._can_handle_task(agent, task)]
        
        if not capable_agents:
            return None
            
        # Sort by priority and load
        if task.priority == Priority.CRITICAL:
            capable_agents.sort(key=lambda x: (x.current_load, x.registered_at))
        else:
            capable_agents.sort(key=lambda x: x.current_load)
            
        selected = capable_agents[0]
        selected.current_load += 1
        
        return selected
        
    def _can_handle_task(self, agent: AgentMetadata, task: AgentTask) -> bool:
        """Check if agent can handle the task"""
        # Check if agent has the required capability
        if task.task_type in agent.capabilities:
            return True
            
        # Check if agent type matches the task type
        agent_type_map = {
            "learning_progress": AgentType.LEARNING_PROGRESS,
            "quiz_generation": AgentType.QUIZ_GENERATOR,
            "code_analysis": AgentType.CODE_ANALYZER,
            "quality_assessment": AgentType.QUALITY_ASSESSOR,
            "content_recommendation": AgentType.CONTENT_RECOMMENDER,
            "analytics": AgentType.ANALYTICS
        }
        
        expected_type = agent_type_map.get(task.task_type)
        return expected_type == agent.agent_type


class AgentOrchestrator:
    """Central orchestration engine for multi-agent coordination"""
    
    def __init__(self, registry: AgentRegistry, assignment_strategy: TaskAssignmentStrategy = None):
        self.registry = registry
        self.assignment_strategy = assignment_strategy or LoadBalancedStrategy()
        self.pending_tasks: Dict[UUID, AgentTask] = {}
        self.running_tasks: Dict[UUID, AgentTask] = {}
        self.completed_tasks: Dict[UUID, AgentTask] = {}
        self._task_queue = asyncio.Queue()
        self._background_tasks: Set[asyncio.Task] = set()
        
    async def start(self):
        """Start the orchestrator"""
        # Start background tasks
        self._background_tasks.add(asyncio.create_task(self._process_tasks()))
        self._background_tasks.add(asyncio.create_task(self._monitor_health()))
        self._background_tasks.add(asyncio.create_task(self._cleanup_tasks()))
        
        logger.info("Agent Orchestrator started")
        
    async def stop(self):
        """Stop the orchestrator gracefully"""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        logger.info("Agent Orchestrator stopped")
        
    async def submit_task(self, task: AgentTask) -> bool:
        """Submit a task for processing"""
        try:
            # Add to pending tasks
            self.pending_tasks[task.task_id] = task
            
            # Add to processing queue
            await self._task_queue.put(task)
            
            logger.info(f"Task {task.task_id} submitted for processing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {str(e)}")
            return False
            
    async def _process_tasks(self):
        """Main task processing loop"""
        while True:
            try:
                # Get task from queue
                task = await self._task_queue.get()
                
                # Find suitable agent
                agents = await self.registry.get_available_agents(
                    self._infer_agent_type(task.task_type)
                )
                
                if not agents:
                    logger.warning(f"No available agents for task {task.task_id}")
                    await asyncio.sleep(1)
                    continue
                    
                # Select best agent
                selected_agent = await self.assignment_strategy.select_agent(agents, task)
                
                if not selected_agent:
                    logger.warning(f"No suitable agent found for task {task.task_id}")
                    continue
                    
                # Update task status
                self.pending_tasks.pop(task.task_id, None)
                self.running_tasks[task.task_id] = task
                
                # Update agent status
                await self.registry.update_agent_status(
                    selected_agent.agent_id, 
                    AgentStatus.BUSY
                )
                
                # Execute task (async, non-blocking)
                asyncio.create_task(self._execute_task(task, selected_agent))
                
            except Exception as e:
                logger.error(f"Error in task processing loop: {str(e)}")
                await asyncio.sleep(1)
                
    async def _execute_task(self, task: AgentTask, agent: AgentMetadata):
        """Execute a task with the selected agent"""
        try:
            logger.info(f"Executing task {task.task_id} on agent {agent.name}")
            
            # Create task payload
            payload = {
                "task_id": str(task.task_id),
                "task_type": task.task_type,
                "priority": task.priority.value,
                "data": task.payload,
                "timeout": task.timeout_seconds
            }
            
            # Publish task to agent via NATS
            await self.registry.nats.publish(
                f"agent.tasks.{agent.agent_id}",
                json.dumps(payload).encode()
            )
            
            # Wait for completion with timeout
            await asyncio.wait_for(self._wait_for_task_completion(task), 
                                 timeout=task.timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task.task_id} timed out")
            await self._handle_task_failure(task, "Timeout")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            await self._handle_task_failure(task, str(e))
            
    async def _wait_for_task_completion(self, task: AgentTask):
        """Wait for task completion via NATS subscription"""
        # This will be implemented with NATS subscriptions
        # For now, simulate task completion
        await asyncio.sleep(2)
        
    async def _handle_task_failure(self, task: AgentTask, error: str):
        """Handle task failure with retry logic"""
        task.retry_count += 1
        
        if task.retry_count < task.max_retries:
            logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count + 1})")
            await self._task_queue.put(task)
        else:
            logger.error(f"Task {task.task_id} failed permanently: {error}")
            # Move to completed tasks for cleanup
            self.completed_tasks[task.task_id] = task
            
    async def _monitor_health(self):
        """Monitor agent health and perform cleanup"""
        while True:
            try:
                # Check for stale agents (no heartbeat in 30 seconds)
                current_time = datetime.now(timezone.utc)
                
                for agent in self.registry.agents.values():
                    if (agent.last_heartbeat and 
                        (current_time - agent.last_heartbeat).total_seconds() > 30):
                        
                        logger.warning(f"Agent {agent.name} heartbeat timeout")
                        await self.registry.update_agent_status(
                            agent.agent_id, AgentStatus.OFFLINE
                        )
                        
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")
                await asyncio.sleep(10)
                
    async def _cleanup_tasks(self):
        """Clean up old completed tasks"""
        while True:
            try:
                # Remove tasks older than 1 hour
                cutoff_time = datetime.now(timezone.utc).timestamp() - 3600
                
                tasks_to_remove = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.created_at.timestamp() < cutoff_time
                ]
                
                for task_id in tasks_to_remove:
                    self.completed_tasks.pop(task_id, None)
                    
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in task cleanup: {str(e)}")
                await asyncio.sleep(300)
                
    def _infer_agent_type(self, task_type: str) -> AgentType:
        """Infer required agent type from task type"""
        type_mapping = {
            "learning_progress": AgentType.LEARNING_PROGRESS,
            "quiz_generation": AgentType.QUIZ_GENERATOR,
            "code_analysis": AgentType.CODE_ANALYZER,
            "quality_assessment": AgentType.QUALITY_ASSESSOR,
            "content_recommendation": AgentType.CONTENT_RECOMMENDER,
            "analytics": AgentType.ANALYTICS
        }
        
        return type_mapping.get(task_type, AgentType.LEARNING_PROGRESS)


# FastAPI Integration
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    redis_client = redis.from_url("redis://localhost:6379")
    nats_client = await nats.connect("nats://localhost:4222")
    
    registry = AgentRegistry(redis_client, nats_client)
    orchestrator = AgentOrchestrator(registry)
    
    # Store in app state
    app.state.registry = registry
    app.state.orchestrator = orchestrator
    
    await orchestrator.start()
    
    yield
    
    # Shutdown
    await orchestrator.stop()
    await nats_client.close()
    await redis_client.close()


# Export main classes
__all__ = [
    "Agent",
    "AgentRegistry", 
    "AgentOrchestrator",
    "AgentMetadata",
    "AgentTask",
    "AgentType",
    "AgentStatus",
    "Priority",
    "LoadBalancedStrategy",
    "PriorityBasedStrategy"
]