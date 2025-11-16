#!/usr/bin/env python3
"""
Jaseci Learning Companion - Agent Registry
Central registry for agent discovery and management

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid

from database.connection import get_db

logger = logging.getLogger(__name__)

@dataclass
class Agent:
    """Agent data structure"""
    agent_id: str
    type: str
    status: str
    capabilities: List[str]
    endpoint_url: Optional[str] = None
    load: float = 0.0
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentRegistry:
    """Enterprise agent registry service"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_timeout = 60  # 60 seconds
    
    async def register_agent(self, agent_info: Dict[str, Any]) -> str:
        """Register new agent"""
        async with self._lock:
            try:
                agent_id = agent_info.get("agent_id") or str(uuid.uuid4())
                
                agent = Agent(
                    agent_id=agent_id,
                    type=agent_info.get("type", "unknown"),
                    status=agent_info.get("status", "available"),
                    capabilities=agent_info.get("capabilities", []),
                    endpoint_url=agent_info.get("endpoint_url"),
                    load=agent_info.get("load", 0.0),
                    last_heartbeat=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    metadata=agent_info.get("metadata", {})
                )
                
                # Store in memory
                self.agents[agent_id] = agent
                
                # Store in database
                await self._store_agent_db(agent)
                
                logger.info(f"Agent registered: {agent_id} ({agent.type})")
                return agent_id
                
            except Exception as e:
                logger.error(f"Error registering agent: {e}")
                raise
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    # Remove from memory
                    del self.agents[agent_id]
                    
                    # Remove from database
                    async with get_db() as conn:
                        await conn.execute("""
                            DELETE FROM agent_registry WHERE agent_id = $1
                        """, agent_id)
                    
                    logger.info(f"Agent unregistered: {agent_id}")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error unregistering agent {agent_id}: {e}")
                return False
    
    async def update_agent_status(self, agent_id: str, status: str, load: float = None) -> bool:
        """Update agent status"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent.status = status
                    agent.last_heartbeat = datetime.utcnow()
                    
                    if load is not None:
                        agent.load = load
                    
                    # Update in database
                    await self._update_agent_db(agent)
                    
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error updating agent {agent_id} status: {e}")
                return False
    
    async def find_suitable_agent(self, task_type: str) -> Optional[str]:
        """Find suitable agent for task type"""
        async with self._lock:
            try:
                suitable_agents = []
                
                for agent_id, agent in self.agents.items():
                    if agent.status == "available" and agent.load < 1.0:
                        # Check if agent can handle this task type
                        if self._can_handle_task(agent, task_type):
                            suitable_agents.append((agent_id, agent))
                
                if not suitable_agents:
                    return None
                
                # Sort by load (lowest first) and select best agent
                suitable_agents.sort(key=lambda x: x[1].load)
                selected_agent_id = suitable_agents[0][0]
                
                # Update agent load
                await self.update_agent_status(selected_agent_id, "busy", 
                                              self.agents[selected_agent_id].load + 0.1)
                
                logger.info(f"Agent {selected_agent_id} selected for task type {task_type}")
                return selected_agent_id
                
            except Exception as e:
                logger.error(f"Error finding suitable agent for {task_type}: {e}")
                return None
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    return asdict(agent)
                return None
                
            except Exception as e:
                logger.error(f"Error getting agent {agent_id}: {e}")
                return None
    
    async def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents"""
        async with self._lock:
            try:
                # Update stale agents
                await self._cleanup_stale_agents()
                
                return {agent_id: asdict(agent) for agent_id, agent in self.agents.items()}
                
            except Exception as e:
                logger.error(f"Error listing agents: {e}")
                return {}
    
    async def get_active_agents_count(self) -> int:
        """Get count of active agents"""
        async with self._lock:
            try:
                await self._cleanup_stale_agents()
                return len(self.agents)
                
            except Exception as e:
                logger.error(f"Error getting active agents count: {e}")
                return 0
    
    async def get_total_agents_count(self) -> int:
        """Get total registered agents count"""
        try:
            async with get_db() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM agent_registry WHERE status != 'unregistered'
                """)
                return count
                
        except Exception as e:
            logger.error(f"Error getting total agents count: {e}")
            return 0
    
    async def get_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get agents by type"""
        async with self._lock:
            try:
                await self._cleanup_stale_agents()
                
                agents_of_type = []
                for agent_id, agent in self.agents.items():
                    if agent.type == agent_type:
                        agents_of_type.append(asdict(agent))
                
                return agents_of_type
                
            except Exception as e:
                logger.error(f"Error getting agents by type {agent_type}: {e}")
                return []
    
    async def heartbeat(self, agent_id: str, status: str = None, load: float = None) -> bool:
        """Agent heartbeat"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent.last_heartbeat = datetime.utcnow()
                    
                    if status:
                        agent.status = status
                    if load is not None:
                        agent.load = load
                    
                    await self._update_agent_db(agent)
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error processing heartbeat for agent {agent_id}: {e}")
                return False
    
    async def get_agent_load(self, agent_id: str) -> Optional[float]:
        """Get agent load"""
        async with self._lock:
            try:
                if agent_id in self.agents:
                    return self.agents[agent_id].load
                return None
                
            except Exception as e:
                logger.error(f"Error getting load for agent {agent_id}: {e}")
                return None
    
    async def initialize_from_database(self):
        """Initialize agents from database"""
        try:
            async with get_db() as conn:
                agents_data = await conn.fetch("""
                    SELECT agent_id, agent_type, status, capabilities, endpoint_url,
                           load_factor, last_heartbeat, metadata
                    FROM agent_registry
                    WHERE status != 'unregistered'
                """)
                
                for agent_data in agents_data:
                    agent = Agent(
                        agent_id=agent_data["agent_id"],
                        type=agent_data["agent_type"],
                        status=agent_data["status"],
                        capabilities=agent_data["capabilities"] or [],
                        endpoint_url=agent_data["endpoint_url"],
                        load=float(agent_data["load_factor"] or 0.0),
                        last_heartbeat=agent_data["last_heartbeat"],
                        created_at=agent_data.get("created_at"),
                        metadata=agent_data["metadata"] or {}
                    )
                    
                    self.agents[agent_data["agent_id"]] = agent
                
                logger.info(f"Loaded {len(self.agents)} agents from database")
                
        except Exception as e:
            logger.error(f"Error initializing agents from database: {e}")
    
    async def close(self):
        """Close registry"""
        logger.info("Agent registry closed")
    
    def _can_handle_task(self, agent: Agent, task_type: str) -> bool:
        """Check if agent can handle task type"""
        # Map task types to agent capabilities
        task_capability_map = {
            "learning_progress": ["progress_tracking", "statistics"],
            "quiz_generator": ["quiz_generation", "question_creation"],
            "code_analysis": ["ccg_analysis", "complexity_analysis"],
            "quality_assessment": ["quality_evaluation", "best_practices"],
            "content_recommendation": ["personalization", "content_matching"],
            "analytics": ["learning_analytics", "engagement_metrics"]
        }
        
        required_capabilities = task_capability_map.get(task_type, [])
        
        # Agent can handle task if it has any of the required capabilities
        return any(cap in agent.capabilities for cap in required_capabilities)
    
    async def _store_agent_db(self, agent: Agent):
        """Store agent in database"""
        async with get_db() as conn:
            await conn.execute("""
                INSERT INTO agent_registry (
                    agent_id, agent_type, status, capabilities, endpoint_url,
                    load_factor, last_heartbeat, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    capabilities = EXCLUDED.capabilities,
                    endpoint_url = EXCLUDED.endpoint_url,
                    load_factor = EXCLUDED.load_factor,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    metadata = EXCLUDED.metadata
            """, agent.agent_id, agent.type, agent.status, agent.capabilities,
                agent.endpoint_url, agent.load, agent.last_heartbeat,
                json.dumps(agent.metadata), agent.created_at)
    
    async def _update_agent_db(self, agent: Agent):
        """Update agent in database"""
        async with get_db() as conn:
            await conn.execute("""
                UPDATE agent_registry
                SET status = $1, load_factor = $2, last_heartbeat = $3, metadata = $4
                WHERE agent_id = $5
            """, agent.status, agent.load, agent.last_heartbeat,
                json.dumps(agent.metadata), agent.agent_id)
    
    async def _cleanup_stale_agents(self):
        """Clean up stale agents"""
        stale_agents = []
        
        for agent_id, agent in self.agents.items():
            if agent.last_heartbeat:
                time_since_heartbeat = datetime.utcnow() - agent.last_heartbeat
                if time_since_heartbeat.total_seconds() > self._heartbeat_timeout:
                    stale_agents.append(agent_id)
        
        for agent_id in stale_agents:
            logger.warning(f"Removing stale agent: {agent_id}")
            del self.agents[agent_id]
            
            # Update database
            async with get_db() as conn:
                await conn.execute("""
                    UPDATE agent_registry
                    SET status = 'stale'
                    WHERE agent_id = $1
                """, agent_id)
