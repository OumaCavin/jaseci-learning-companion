#!/usr/bin/env python3
"""
Jaseci Learning Companion - Task Scheduler
Scheduled task management and execution

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScheduleType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CRON = "cron"

@dataclass
class ScheduledTask:
    """Scheduled task data structure"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    schedule_time: datetime
    schedule_type: ScheduleType
    status: TaskStatus
    created_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    handler: Optional[Callable] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskScheduler:
    """Enterprise task scheduler service"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start task scheduler"""
        if not self._running:
            self._running = True
            self._scheduler_task = asyncio.create_task(self._schedule_loop())
            logger.info("Task scheduler started")
    
    async def stop(self):
        """Stop task scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        logger.info("Task scheduler stopped")
    
    async def schedule_task(self, task: ScheduledTask) -> str:
        """Schedule a task"""
        async with self._lock:
            try:
                task_id = task.task_id or str(uuid.uuid4())
                task.task_id = task_id
                
                # Store in memory
                self.scheduled_tasks[task_id] = task
                
                # Store in Redis for persistence
                await self._store_task_redis(task)
                
                logger.info(f"Task scheduled: {task_id} for {task.schedule_time}")
                return task_id
                
            except Exception as e:
                logger.error(f"Error scheduling task: {e}")
                raise
    
    async def schedule_one_time_task(self, task_type: str, payload: Dict[str, Any], 
                                   run_time: datetime, handler: Callable = None) -> str:
        """Schedule one-time task"""
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            schedule_time=run_time,
            schedule_type=ScheduleType.ONE_TIME,
            status=TaskStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            handler=handler
        )
        
        return await self.schedule_task(task)
    
    async def schedule_recurring_task(self, task_type: str, payload: Dict[str, Any],
                                    interval: timedelta, start_time: datetime = None,
                                    max_runs: int = None, handler: Callable = None) -> str:
        """Schedule recurring task"""
        if start_time is None:
            start_time = datetime.utcnow()
        
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            schedule_time=start_time,
            schedule_type=ScheduleType.RECURRING,
            status=TaskStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            max_runs=max_runs,
            handler=handler
        )
        
        return await self.schedule_task(task)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel scheduled task"""
        async with self._lock:
            try:
                if task_id in self.scheduled_tasks:
                    task = self.scheduled_tasks[task_id]
                    task.status = TaskStatus.CANCELLED
                    
                    # Cancel running instance
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id].cancel()
                        del self.running_tasks[task_id]
                    
                    # Update in Redis
                    await self._update_task_redis(task)
                    
                    logger.info(f"Task cancelled: {task_id}")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error cancelling task {task_id}: {e}")
                return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled task"""
        async with self._lock:
            try:
                if task_id in self.scheduled_tasks:
                    return asdict(self.scheduled_tasks[task_id])
                return None
                
            except Exception as e:
                logger.error(f"Error getting task {task_id}: {e}")
                return None
    
    async def list_tasks(self, status: TaskStatus = None, task_type: str = None) -> List[Dict[str, Any]]:
        """List scheduled tasks"""
        async with self._lock:
            try:
                tasks = list(self.scheduled_tasks.values())
                
                if status:
                    tasks = [task for task in tasks if task.status == status]
                
                if task_type:
                    tasks = [task for task in tasks if task.task_type == task_type]
                
                # Sort by schedule time
                tasks.sort(key=lambda t: t.schedule_time)
                
                return [asdict(task) for task in tasks]
                
            except Exception as e:
                logger.error(f"Error listing tasks: {e}")
                return []
    
    async def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get tasks ready to run"""
        async with self._lock:
            try:
                now = datetime.utcnow()
                pending = []
                
                for task in self.scheduled_tasks.values():
                    if (task.status == TaskStatus.SCHEDULED and 
                        task.schedule_time <= now and
                        task.task_id not in self.running_tasks):
                        pending.append(task)
                
                return pending
                
            except Exception as e:
                logger.error(f"Error getting pending tasks: {e}")
                return []
    
    async def get_task_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics"""
        async with self._lock:
            try:
                total_tasks = len(self.scheduled_tasks)
                running_tasks = len(self.running_tasks)
                
                status_counts = {}
                for task in self.scheduled_tasks.values():
                    status = task.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                type_counts = {}
                for task in self.scheduled_tasks.values():
                    task_type = task.task_type
                    type_counts[task_type] = type_counts.get(task_type, 0) + 1
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_tasks": total_tasks,
                    "running_tasks": running_tasks,
                    "status_distribution": status_counts,
                    "type_distribution": type_counts
                }
                
            except Exception as e:
                logger.error(f"Error getting task metrics: {e}")
                return {}
    
    async def initialize_from_redis(self):
        """Initialize tasks from Redis"""
        try:
            # Get all scheduled tasks from Redis
            task_keys = await self.redis_client.keys("scheduled_task:*")
            
            for key in task_keys:
                task_data = await self.redis_client.get(key)
                if task_data:
                    try:
                        task_dict = json.loads(task_data)
                        
                        # Convert datetime strings back to datetime objects
                        for field in ["schedule_time", "created_at", "last_run", "next_run"]:
                            if field in task_dict and task_dict[field]:
                                try:
                                    task_dict[field] = datetime.fromisoformat(task_dict[field])
                                except ValueError:
                                    pass
                        
                        task = ScheduledTask(**task_dict)
                        
                        # Only include if it's still in the future or recently scheduled
                        if task.schedule_time > datetime.utcnow() - timedelta(days=7):
                            self.scheduled_tasks[task.task_id] = task
                        
                    except Exception as e:
                        logger.error(f"Error loading task from Redis: {e}")
            
            logger.info(f"Loaded {len(self.scheduled_tasks)} tasks from Redis")
            
        except Exception as e:
            logger.error(f"Error initializing tasks from Redis: {e}")
    
    async def close(self):
        """Close scheduler"""
        await self.stop()
        logger.info("Task scheduler closed")
    
    async def _schedule_loop(self):
        """Main scheduling loop"""
        while self._running:
            try:
                # Get pending tasks
                pending_tasks = await self.get_pending_tasks()
                
                for task in pending_tasks:
                    await self._execute_task(task)
                
                # Sleep for a short period
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(5)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute scheduled task"""
        try:
            # Mark as running
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.utcnow()
            task.run_count += 1
            
            # Add to running tasks
            execution_task = asyncio.create_task(self._run_task_handler(task))
            self.running_tasks[task.task_id] = execution_task
            
            # Update in Redis
            await self._update_task_redis(task)
            
            logger.info(f"Executing task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            await self._update_task_redis(task)
    
    async def _run_task_handler(self, task: ScheduledTask):
        """Run task handler"""
        try:
            if task.handler:
                # Execute custom handler
                if asyncio.iscoroutinefunction(task.handler):
                    await task.handler(task)
                else:
                    task.handler(task)
            else:
                # Execute default task processing
                await self._default_task_handler(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            
            # Handle recurring tasks
            if task.schedule_type == ScheduleType.RECURRING:
                if task.max_runs and task.run_count >= task.max_runs:
                    task.status = TaskStatus.COMPLETED
                else:
                    # Reschedule for next interval
                    task.schedule_time = task.last_run + timedelta(
                        seconds=task.payload.get("interval_seconds", 3600)
                    )
                    task.status = TaskStatus.SCHEDULED
            
            await self._update_task_redis(task)
            
        except Exception as e:
            logger.error(f"Error in task handler for {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            await self._update_task_redis(task)
        
        finally:
            # Remove from running tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    async def _default_task_handler(self, task: ScheduledTask):
        """Default task handler"""
        # Default implementation - could be extended or replaced
        logger.info(f"Running default handler for task {task.task_id}: {task.task_type}")
        
        # Simulate task execution
        await asyncio.sleep(1)
        
        # Log task execution
        logger.info(f"Default task completed: {task.task_id}")
    
    async def _store_task_redis(self, task: ScheduledTask):
        """Store task in Redis"""
        try:
            task_data = json.dumps(asdict(task), default=str)
            key = f"scheduled_task:{task.task_id}"
            
            await self.redis_client.set(key, task_data)
            
            # Set expiry based on schedule time
            if task.schedule_time:
                ttl = int((task.schedule_time - datetime.utcnow()).total_seconds()) + 3600  # +1 hour buffer
                if ttl > 0:
                    await self.redis_client.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"Error storing task {task.task_id} in Redis: {e}")
    
    async def _update_task_redis(self, task: ScheduledTask):
        """Update task in Redis"""
        try:
            task_data = json.dumps(asdict(task), default=str)
            key = f"scheduled_task:{task.task_id}"
            
            await self.redis_client.set(key, task_data)
            
        except Exception as e:
            logger.error(f"Error updating task {task.task_id} in Redis: {e}")
