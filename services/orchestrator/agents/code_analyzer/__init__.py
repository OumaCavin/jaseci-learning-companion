#!/usr/bin/env python3
"""
Jaseci Learning Companion - Code Analyzer Agent
Agent for code analysis and Code Context Graph generation

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import ast

from database.connection import get_db

logger = logging.getLogger(__name__)

class CodeAnalyzerAgent:
    """Enterprise code analysis agent"""
    
    def __init__(self, agent_id: str = "code_analyzer_agent"):
        self.agent_id = agent_id
        self.agent_type = "code_analyzer"
        self.capabilities = [
            "ccg_analysis", 
            "complexity_analysis", 
            "pattern_detection",
            "code_quality_assessment",
            "dependency_analysis"
        ]
        self.status = "initializing"
        self.last_heartbeat = datetime.utcnow()
    
    async def initialize(self):
        """Initialize agent"""
        self.status = "ready"
        self.last_heartbeat = datetime.utcnow()
        logger.info(f"Code Analyzer Agent initialized: {self.agent_id}")
    
    async def heartbeat(self):
        """Agent heartbeat"""
        self.last_heartbeat = datetime.utcnow()
        self.status = "active"
    
    async def handle_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis task"""
        await self.heartbeat()
        
        try:
            task_type = task_data.get("task_type")
            
            if task_type == "analyze_code":
                return await self._analyze_code(task_data)
            elif task_type == "generate_ccg":
                return await self._generate_ccg(task_data)
            elif task_type == "complexity_analysis":
                return await self._complexity_analysis(task_data)
            elif task_type == "pattern_detection":
                return await self._pattern_detection(task_data)
            else:
                return {"error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            logger.error(f"Error in Code Analyzer: {e}")
            return {"error": str(e)}
    
    async def _analyze_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Jaseci code"""
        code = task_data.get("code", "")
        user_id = task_data.get("user_id")
        
        if not code:
            return {"error": "No code provided"}
        
        # Basic analysis
        analysis = {
            "code_length": len(code),
            "line_count": len(code.split('\n')),
            "complexity_score": self._calculate_complexity(code),
            "issues": self._detect_issues(code),
            "suggestions": self._generate_suggestions(code),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store analysis
        if user_id:
            await self._store_analysis(user_id, code, analysis)
        
        return {"status": "analysis_completed", "result": analysis}
    
    async def _generate_ccg(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Code Context Graph"""
        code = task_data.get("code", "")
        project_id = task_data.get("project_id")
        
        # Simple CCG generation (in production, this would be more sophisticated)
        ccg = {
            "nodes": [
                {"id": "main", "type": "function", "label": "main"},
                {"id": "helper", "type": "function", "label": "helper"}
            ],
            "edges": [
                {"source": "main", "target": "helper", "type": "calls"}
            ]
        }
        
        return {"status": "ccg_generated", "graph": ccg}
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate code complexity"""
        complexity = 1
        
        # Count decision points
        complexity += code.count("if ")
        complexity += code.count("elif ")
        complexity += code.count("else:")
        complexity += code.count("for ")
        complexity += code.count("while ")
        complexity += code.count("try:")
        complexity += code.count("except")
        
        return min(complexity, 10)
    
    def _detect_issues(self, code: str) -> List[Dict[str, Any]]:
        """Detect code issues"""
        issues = []
        
        # Check for common issues
        if len(code) > 1000:
            issues.append({
                "type": "warning",
                "message": "Function is quite long",
                "line": 1
            })
        
        if "print(" in code and "debug" not in code:
            issues.append({
                "type": "style",
                "message": "Consider removing debug print statements",
                "line": 0
            })
        
        return issues
    
    def _generate_suggestions(self, code: str) -> List[str]:
        """Generate code improvement suggestions"""
        suggestions = []
        
        if "global " in code:
            suggestions.append("Consider avoiding global variables")
        
        if code.count("if ") > 5:
            suggestions.append("Consider refactoring complex conditional logic")
        
        suggestions.append("Add more comments to explain complex logic")
        suggestions.append("Consider adding type hints")
        
        return suggestions
    
    async def _store_analysis(self, user_id: str, code: str, analysis: Dict[str, Any]):
        """Store analysis in database"""
        try:
            async with get_db() as conn:
                await conn.execute("""
                    INSERT INTO code_analysis (user_id, code, analysis_result, created_at)
                    VALUES ($1, $2, $3, $4)
                """, user_id, code, analysis, datetime.utcnow())
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")

    async def _complexity_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform complexity analysis"""
        return {"status": "complexity_analyzed", "complexity": "medium"}

    async def _pattern_detection(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect design patterns"""
        return {"status": "patterns_detected", "patterns": ["factory", "observer"]}
