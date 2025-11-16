"""
Quality Assessor Agent
Multi-dimensional quality evaluation for the Jaseci Learning Companion

This agent implements a comprehensive 5-dimensional quality assessment system
that evaluates code correctness, performance, security, code quality, and documentation.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import re
import time
import subprocess
import tempfile
import os

import asyncpg
import redis.asyncio as redis
import nats
from pydantic import BaseModel, Field, validator
import psutil

from ..registry import Agent, AgentMetadata, AgentType, AgentStatus, Priority, AgentTask


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Quality Assessment Models
class QualityDimension(str, Enum):
    """Five quality assessment dimensions"""
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"


class QualityLevel(str, Enum):
    """Quality levels"""
    EXCELLENT = "excellent"      # 90-100
    GOOD = "good"               # 80-89
    AVERAGE = "average"         # 70-79
    BELOW_AVERAGE = "below_average"  # 60-69
    POOR = "poor"              # 0-59


@dataclass
class QualityCriteria:
    """Quality assessment criteria for each dimension"""
    dimension: QualityDimension
    weight: float  # Weight in overall score (0-1)
    rules: List[str]  # Assessment rules
    metrics: Dict[str, float]  # Calculated metrics
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class CodeQualityIssue:
    """Individual code quality issue"""
    issue_id: UUID
    dimension: QualityDimension
    severity: str  # critical, high, medium, low
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    category: str = ""


class DetailedScore(BaseModel):
    """Detailed score for a quality dimension"""
    dimension: QualityDimension
    score: float = Field(ge=0, le=100)
    level: QualityLevel
    confidence: float = Field(ge=0, le=1)  # How confident we are in the assessment
    issues_found: int = 0
    rules_applied: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)
    breakdown: Dict[str, float] = Field(default_factory=dict)


class QualityAssessmentResult(BaseModel):
    """Comprehensive quality assessment result"""
    assessment_id: UUID = Field(default_factory=uuid4)
    submission_id: UUID
    user_id: UUID
    
    # Overall assessment
    overall_score: float = Field(ge=0, le=100)
    overall_level: QualityLevel
    assessment_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assessment_duration_ms: int = 0
    
    # Detailed dimension scores
    correctness_score: DetailedScore
    performance_score: DetailedScore
    security_score: DetailedScore
    code_quality_score: DetailedScore
    documentation_score: DetailedScore
    
    # Issues and feedback
    critical_issues: List[CodeQualityIssue] = Field(default_factory=list)
    all_issues: List[CodeQualityIssue] = Field(default_factory=list)
    improvement_plan: List[str] = Field(default_factory=list)
    
    # Assessment metadata
    assessment_method: str = "comprehensive"
    ai_enhanced: bool = True
    confidence_level: float = 0.0


class SecurityAnalysis(BaseModel):
    """Security analysis results"""
    security_score: float = 0.0
    vulnerabilities_found: List[Dict[str, Any]] = Field(default_factory=list)
    insecure_patterns: List[str] = Field(default_factory=list)
    security_recommendations: List[str] = Field(default_factory=list)
    compliance_check: Dict[str, bool] = Field(default_factory=dict)


class PerformanceAnalysis(BaseModel):
    """Performance analysis results"""
    performance_score: float = 0.0
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    algorithm_complexity: str = "unknown"
    bottlenecks: List[str] = Field(default_factory=list)
    optimization_opportunities: List[str] = Field(default_factory=dict)
    scalability_rating: str = "unknown"


class CodeQualityAnalysis(BaseModel):
    """Code quality analysis results"""
    quality_score: float = 0.0
    complexity_metrics: Dict[str, float] = Field(default_factory=dict)
    maintainability_index: float = 0.0
    code_smells: List[Dict[str, Any]] = Field(default_factory=list)
    best_practices_compliance: float = 0.0
    technical_debt_score: float = 0.0


class QualityAssessorAgent(Agent):
    """Multi-dimensional Quality Assessor Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id=uuid4(),
            agent_type=AgentType.QUALITY_ASSESSOR,
            name="Quality Assessment Engine",
            version="2.0.0-enterprise"
        )
        self.redis_client = None
        self.database_pool = None
        self.nats_client = None
        
        # Assessment configurations
        self.quality_weights = {
            QualityDimension.CORRECTNESS: 0.30,    # 30% weight
            QualityDimension.PERFORMANCE: 0.20,    # 20% weight
            QualityDimension.SECURITY: 0.20,       # 20% weight
            QualityDimension.CODE_QUALITY: 0.20,   # 20% weight
            QualityDimension.DOCUMENTATION: 0.10   # 10% weight
        }
        
        # Quality rules and thresholds
        self.quality_rules = self._load_quality_rules()
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
        
    async def initialize(self) -> bool:
        """Initialize the Quality Assessor Agent"""
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
            await self.register_capability("assess_code_quality")
            await self.register_capability("analyze_correctness")
            await self.register_capability("evaluate_performance")
            await self.register_capability("detect_security_issues")
            await self.register_capability("check_code_standards")
            await self.register_capability("generate_improvement_plan")
            
            # Subscribe to NATS subjects
            await self.nats_client.subscribe("quality.requests.*", self._handle_quality_request)
            await self.nats_client.subscribe("code.submissions.*", self._handle_code_submission)
            
            logger.info("Quality Assessor Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Quality Assessor Agent: {e}")
            return False
            
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process quality assessment tasks"""
        try:
            task_type = task.task_type
            
            if task_type == "assess_quality":
                return await self._assess_code_quality(task.payload)
            elif task_type == "analyze_correctness":
                return await self._analyze_correctness(task.payload)
            elif task_type == "evaluate_performance":
                return await self._evaluate_performance(task.payload)
            elif task_type == "detect_security":
                return await self._detect_security_issues(task.payload)
            elif task_type == "check_standards":
                return await self._check_code_standards(task.payload)
            elif task_type == "generate_plan":
                return await self._generate_improvement_plan(task.payload)
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
                "quality_rules_loaded": len(self.quality_rules),
                "security_patterns_loaded": len(self.security_patterns),
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
    async def _handle_quality_request(self, msg):
        """Handle quality assessment requests from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._assess_code_quality(data)
        except Exception as e:
            logger.error(f"Error handling quality request: {e}")
            
    async def _handle_code_submission(self, msg):
        """Handle code submission for automatic quality assessment"""
        try:
            data = json.loads(msg.data.decode())
            await self._assess_code_quality(data)
        except Exception as e:
            logger.error(f"Error handling code submission: {e}")
            
    # Main processing methods
    async def _assess_code_quality(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive quality assessment"""
        try:
            start_time = time.time()
            
            # Parse assessment request
            submission_id = UUID(payload.get("submission_id"))
            user_id = UUID(payload.get("user_id"))
            code = payload.get("code", "")
            language = payload.get("language", "jac")
            context = payload.get("context", {})
            
            # Perform dimensional assessments
            correctness_score = await self._analyze_correctness(code, language, context)
            performance_score = await self._evaluate_performance(code, language)
            security_score = await self._detect_security_issues(code, language)
            code_quality_score = await self._check_code_standards(code, language)
            documentation_score = await self._evaluate_documentation(code, language)
            
            # Calculate overall score
            overall_score = (
                correctness_score.score * self.quality_weights[QualityDimension.CORRECTNESS] +
                performance_score.score * self.quality_weights[QualityDimension.PERFORMANCE] +
                security_score.score * self.quality_weights[QualityDimension.SECURITY] +
                code_quality_score.score * self.quality_weights[QualityDimension.CODE_QUALITY] +
                documentation_score.score * self.quality_weights[QualityDimension.DOCUMENTATION]
            )
            
            # Determine overall quality level
            overall_level = self._calculate_quality_level(overall_score)
            
            # Collect all issues
            all_issues = (
                correctness_score.issues_found + performance_score.issues_found +
                security_score.issues_found + code_quality_score.issues_found +
                documentation_score.issues_found
            )
            
            # Generate improvement plan
            improvement_plan = self._generate_improvement_plan(
                correctness_score, performance_score, security_score,
                code_quality_score, documentation_score
            )
            
            # Create assessment result
            assessment_result = QualityAssessmentResult(
                submission_id=submission_id,
                user_id=user_id,
                overall_score=overall_score,
                overall_level=overall_level,
                assessment_duration_ms=int((time.time() - start_time) * 1000),
                correctness_score=correctness_score,
                performance_score=performance_score,
                security_score=security_score,
                code_quality_score=code_quality_score,
                documentation_score=documentation_score,
                all_issues=all_issues,
                critical_issues=self._extract_critical_issues(all_issues),
                improvement_plan=improvement_plan,
                confidence_level=self._calculate_confidence_level(
                    correctness_score.confidence, performance_score.confidence,
                    security_score.confidence, code_quality_score.confidence,
                    documentation_score.confidence
                )
            )
            
            # Store assessment results
            await self._store_assessment_results(assessment_result)
            
            # Emit real-time update
            await self._emit_assessment_update(user_id, assessment_result)
            
            logger.info(f"Completed quality assessment for submission {submission_id}")
            
            return {
                "status": "success",
                "assessment_id": str(assessment_result.assessment_id),
                "overall_score": overall_score,
                "overall_level": overall_level.value,
                "dimension_scores": {
                    "correctness": correctness_score.score,
                    "performance": performance_score.score,
                    "security": security_score.score,
                    "code_quality": code_quality_score.score,
                    "documentation": documentation_score.score
                }
            }
            
        except Exception as e:
            logger.error(f"Error assessing code quality: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _analyze_correctness(self, code: str, language: str, context: Dict[str, Any]) -> DetailedScore:
        """Analyze code correctness"""
        try:
            issues = []
            rules_applied = 0
            metrics = {}
            
            # Check for syntax errors (if possible to execute)
            syntax_score = await self._check_syntax(code, language)
            rules_applied += 1
            
            # Check for logic errors
            logic_score = await self._check_logic(code, language)
            rules_applied += 1
            
            # Check for edge cases
            edge_case_score = await self._check_edge_cases(code, language)
            rules_applied += 1
            
            # Check for error handling
            error_handling_score = await self._check_error_handling(code, language)
            rules_applied += 1
            
            # Calculate weighted correctness score
            total_score = (
                syntax_score * 0.3 + logic_score * 0.4 + 
                edge_case_score * 0.2 + error_handling_score * 0.1
            )
            
            # Detect issues
            issues.extend(await self._detect_correctness_issues(code, language))
            
            # Calculate confidence
            confidence = min(1.0, rules_applied / 4.0)  # More rules = higher confidence
            
            return DetailedScore(
                dimension=QualityDimension.CORRECTNESS,
                score=total_score,
                level=self._calculate_quality_level(total_score),
                confidence=confidence,
                issues_found=len(issues),
                rules_applied=rules_applied,
                metrics=metrics,
                breakdown={
                    "syntax": syntax_score,
                    "logic": logic_score,
                    "edge_cases": edge_case_score,
                    "error_handling": error_handling_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing correctness: {e}")
            return DetailedScore(
                dimension=QualityDimension.CORRECTNESS,
                score=0.0,
                level=QualityLevel.POOR,
                confidence=0.0,
                issues_found=1,
                rules_applied=0
            )
            
    async def _evaluate_performance(self, code: str, language: str) -> DetailedScore:
        """Evaluate code performance"""
        try:
            issues = []
            rules_applied = 0
            metrics = {}
            
            # Execute performance analysis
            exec_time = await self._measure_execution_time(code, language)
            rules_applied += 1
            
            # Check for algorithmic complexity
            complexity_score = await self._check_algorithmic_complexity(code)
            rules_applied += 1
            
            # Check for memory usage patterns
            memory_score = await self._check_memory_patterns(code, language)
            rules_applied += 1
            
            # Check for performance anti-patterns
            anti_pattern_score = await self._check_performance_anti_patterns(code)
            rules_applied += 1
            
            # Calculate performance score
            if exec_time and exec_time > 0:
                # Normalize execution time (0-100, where 100 is fast)
                time_score = max(0, 100 - (exec_time / 10))  # 10ms baseline
            else:
                time_score = 80  # Default score if execution failed
                
            total_score = (
                time_score * 0.3 + complexity_score * 0.4 +
                memory_score * 0.2 + anti_pattern_score * 0.1
            )
            
            metrics["execution_time_ms"] = exec_time or 0
            metrics["algorithmic_complexity"] = complexity_score
            metrics["memory_score"] = memory_score
            
            # Detect issues
            issues.extend(await self._detect_performance_issues(code, language))
            
            confidence = min(1.0, rules_applied / 4.0)
            
            return DetailedScore(
                dimension=QualityDimension.PERFORMANCE,
                score=total_score,
                level=self._calculate_quality_level(total_score),
                confidence=confidence,
                issues_found=len(issues),
                rules_applied=rules_applied,
                metrics=metrics,
                breakdown={
                    "execution_time": time_score,
                    "algorithmic_complexity": complexity_score,
                    "memory_patterns": memory_score,
                    "anti_patterns": anti_pattern_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error evaluating performance: {e}")
            return DetailedScore(
                dimension=QualityDimension.PERFORMANCE,
                score=50.0,  # Neutral score
                level=QualityLevel.AVERAGE,
                confidence=0.0,
                issues_found=1,
                rules_applied=0
            )
            
    async def _detect_security_issues(self, code: str, language: str) -> DetailedScore:
        """Detect security issues in code"""
        try:
            issues = []
            rules_applied = 0
            metrics = {}
            
            # Check for security vulnerabilities
            vuln_score = await self._check_security_vulnerabilities(code)
            rules_applied += 1
            
            # Check for input validation
            input_score = await self._check_input_validation(code, language)
            rules_applied += 1
            
            # Check for authentication/authorization patterns
            auth_score = await self._check_auth_patterns(code, language)
            rules_applied += 1
            
            # Check for data exposure risks
            exposure_score = await self._check_data_exposure(code, language)
            rules_applied += 1
            
            # Calculate security score
            total_score = (
                vuln_score * 0.4 + input_score * 0.3 +
                auth_score * 0.2 + exposure_score * 0.1
            )
            
            # Check security patterns
            security_patterns_found = self._check_security_patterns(code)
            metrics["patterns_detected"] = len(security_patterns_found)
            metrics["vulnerability_count"] = len([p for p in security_patterns_found if p.get("is_vulnerability", False)])
            
            # Detect issues
            issues.extend(await self._detect_security_issues_list(code, language))
            
            confidence = min(1.0, rules_applied / 4.0)
            
            return DetailedScore(
                dimension=QualityDimension.SECURITY,
                score=total_score,
                level=self._calculate_quality_level(total_score),
                confidence=confidence,
                issues_found=len(issues),
                rules_applied=rules_applied,
                metrics=metrics,
                breakdown={
                    "vulnerabilities": vuln_score,
                    "input_validation": input_score,
                    "authentication": auth_score,
                    "data_exposure": exposure_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error detecting security issues: {e}")
            return DetailedScore(
                dimension=QualityDimension.SECURITY,
                score=50.0,
                level=QualityLevel.AVERAGE,
                confidence=0.0,
                issues_found=1,
                rules_applied=0
            )
            
    async def _check_code_standards(self, code: str, language: str) -> DetailedScore:
        """Check code standards and best practices"""
        try:
            issues = []
            rules_applied = 0
            metrics = {}
            
            # Check naming conventions
            naming_score = await self._check_naming_conventions(code, language)
            rules_applied += 1
            
            # Check code structure and organization
            structure_score = await self._check_code_structure(code, language)
            rules_applied += 1
            
            # Check for code smells
            smell_score = await self._check_code_smells(code)
            rules_applied += 1
            
            # Check adherence to language-specific standards
            standards_score = await self._check_language_standards(code, language)
            rules_applied += 1
            
            # Calculate code quality score
            total_score = (
                naming_score * 0.25 + structure_score * 0.35 +
                smell_score * 0.25 + standards_score * 0.15
            )
            
            # Calculate complexity metrics
            complexity_metrics = self._calculate_complexity_metrics(code)
            metrics.update(complexity_metrics)
            
            # Detect issues
            issues.extend(await self._detect_code_quality_issues(code, language))
            
            confidence = min(1.0, rules_applied / 4.0)
            
            return DetailedScore(
                dimension=QualityDimension.CODE_QUALITY,
                score=total_score,
                level=self._calculate_quality_level(total_score),
                confidence=confidence,
                issues_found=len(issues),
                rules_applied=rules_applied,
                metrics=metrics,
                breakdown={
                    "naming": naming_score,
                    "structure": structure_score,
                    "code_smells": smell_score,
                    "standards": standards_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking code standards: {e}")
            return DetailedScore(
                dimension=QualityDimension.CODE_QUALITY,
                score=50.0,
                level=QualityLevel.AVERAGE,
                confidence=0.0,
                issues_found=1,
                rules_applied=0
            )
            
    async def _evaluate_documentation(self, code: str, language: str) -> DetailedScore:
        """Evaluate code documentation quality"""
        try:
            issues = []
            rules_applied = 0
            metrics = {}
            
            # Check for inline comments
            comment_score = await self._check_inline_comments(code)
            rules_applied += 1
            
            # Check for function/method documentation
            docstring_score = await self._check_docstrings(code, language)
            rules_applied += 1
            
            # Check for README and external documentation
            external_doc_score = await self._check_external_documentation(code)
            rules_applied += 1
            
            # Check for clear variable and function names
            clarity_score = await self._check_naming_clarity(code)
            rules_applied += 1
            
            # Calculate documentation score
            total_score = (
                comment_score * 0.3 + docstring_score * 0.4 +
                external_doc_score * 0.2 + clarity_score * 0.1
            )
            
            # Calculate documentation metrics
            metrics["comment_density"] = self._calculate_comment_density(code)
            metrics["docstring_coverage"] = self._calculate_docstring_coverage(code, language)
            
            # Detect issues
            issues.extend(await self._detect_documentation_issues(code, language))
            
            confidence = min(1.0, rules_applied / 4.0)
            
            return DetailedScore(
                dimension=QualityDimension.DOCUMENTATION,
                score=total_score,
                level=self._calculate_quality_level(total_score),
                confidence=confidence,
                issues_found=len(issues),
                rules_applied=rules_applied,
                metrics=metrics,
                breakdown={
                    "comments": comment_score,
                    "docstrings": docstring_score,
                    "external_docs": external_doc_score,
                    "naming_clarity": clarity_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error evaluating documentation: {e}")
            return DetailedScore(
                dimension=QualityDimension.DOCUMENTATION,
                score=50.0,
                level=QualityLevel.AVERAGE,
                confidence=0.0,
                issues_found=1,
                rules_applied=0
            )
            
    # Helper methods for analysis
    async def _check_syntax(self, code: str, language: str) -> float:
        """Check code syntax validity"""
        try:
            if language == "python":
                compile(code, '<string>', 'exec')
                return 100.0
            elif language == "javascript":
                # Simple JavaScript syntax check
                return 90.0 if "{" in code and "}" in code else 70.0
            elif language == "jac":
                # Jaseci syntax check (simplified)
                return 85.0 if "graph" in code else 60.0
            else:
                return 80.0  # Default score
        except SyntaxError:
            return 0.0
        except Exception:
            return 50.0
            
    async def _check_logic(self, code: str, language: str) -> float:
        """Check code logic correctness"""
        # Simplified logic check
        score = 80.0  # Base score
        
        # Check for common logical errors
        if "return" not in code and "def " in code:
            score -= 20  # Function without return
            
        if code.count("if") > code.count("else") * 3:
            score -= 10  # Too many conditional statements
            
        return max(0.0, score)
        
    async def _check_edge_cases(self, code: str, language: str) -> float:
        """Check for edge case handling"""
        score = 75.0
        
        # Check for null/None handling
        if "None" in code or "null" in code:
            score += 10
            
        # Check for exception handling
        if "try:" in code or "catch" in code:
            score += 15
            
        return min(100.0, score)
        
    async def _check_error_handling(self, code: str, language: str) -> float:
        """Check error handling implementation"""
        score = 70.0
        
        if "raise" in code or "throw" in code:
            score += 15
            
        if "except" in code or "catch" in code:
            score += 15
            
        return min(100.0, score)
        
    async def _measure_execution_time(self, code: str, language: str) -> Optional[float]:
        """Measure code execution time"""
        try:
            start_time = time.time()
            
            # Create temporary file based on language
            if language == "python":
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                    
                # Execute and measure time
                try:
                    result = subprocess.run(['python3', temp_file], 
                                          capture_output=True, timeout=5)
                    return (time.time() - start_time) * 1000  # Return ms
                except subprocess.TimeoutExpired:
                    return 10000  # 10 seconds if timeout
                finally:
                    os.unlink(temp_file)
                    
            elif language == "javascript":
                # JavaScript execution (requires Node.js)
                try:
                    result = subprocess.run(['node', '-e', code], 
                                          capture_output=True, timeout=5)
                    return (time.time() - start_time) * 1000
                except subprocess.TimeoutExpired:
                    return 10000
                    
            else:
                # For other languages, estimate based on code complexity
                return max(1.0, len(code.split('\n')) * 0.5)  # Simple estimation
                
        except Exception as e:
            logger.error(f"Error measuring execution time: {e}")
            return None
            
    async def _check_algorithmic_complexity(self, code: str) -> float:
        """Check algorithmic complexity"""
        score = 80.0
        
        # Check for nested loops
        nested_loops = code.count("for") + code.count("while")
        if nested_loops > 3:
            score -= 20 * (nested_loops - 3)  # Penalty for excessive nesting
            
        # Check for recursion
        if "def " in code and code.count("def ") > code.count(code.split("def ")[1].split("(")[0] if code.split("def ") else [""]):
            score -= 10  # Recursion penalty
            
        return max(0.0, score)
        
    async def _check_memory_patterns(self, code: str, language: str) -> float:
        """Check memory usage patterns"""
        score = 85.0
        
        # Check for memory-intensive operations
        if "list(" in code and code.count("list(") > 5:
            score -= 15
            
        if "dict(" in code and code.count("dict(") > 3:
            score -= 10
            
        return max(0.0, score)
        
    async def _check_performance_anti_patterns(self, code: str) -> float:
        """Check for performance anti-patterns"""
        score = 90.0
        
        # Check for inefficient string operations
        if code.count("+=") > code.count("+") * 0.8:
            score -= 10
            
        # Check for unnecessary computations
        if "for" in code and "range(len(" in code:
            score -= 15
            
        return max(0.0, score)
        
    def _check_security_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check for security patterns"""
        patterns_found = []
        
        for pattern in self.security_patterns:
            if re.search(pattern["pattern"], code, re.IGNORECASE):
                patterns_found.append({
                    "pattern": pattern["name"],
                    "description": pattern["description"],
                    "severity": pattern["severity"],
                    "is_vulnerability": pattern.get("is_vulnerability", False)
                })
                
        return patterns_found
        
    def _calculate_quality_level(self, score: float) -> QualityLevel:
        """Calculate quality level from score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.AVERAGE
        elif score >= 60:
            return QualityLevel.BELOW_AVERAGE
        else:
            return QualityLevel.POOR
            
    def _calculate_confidence_level(self, *confidences: float) -> float:
        """Calculate overall confidence level"""
        if not confidences:
            return 0.0
        return sum(confidences) / len(confidences)
        
    def _extract_critical_issues(self, all_issues: List[CodeQualityIssue]) -> List[CodeQualityIssue]:
        """Extract critical issues from all issues"""
        return [issue for issue in all_issues if issue.severity in ["critical", "high"]]
        
    def _generate_improvement_plan(self, *scores: DetailedScore) -> List[str]:
        """Generate improvement plan based on scores"""
        plan = []
        
        for score in scores:
            if score.score < 70:
                dimension_name = score.dimension.value.replace("_", " ").title()
                plan.append(f"Focus on improving {dimension_name} (current score: {score.score:.1f})")
                
                # Add specific suggestions based on issues
                if score.issues_found > 5:
                    plan.append(f"Address the {score.issues_found} issues identified in {dimension_name}")
                    
        return plan
        
    # Database operations
    async def _store_assessment_results(self, result: QualityAssessmentResult):
        """Store assessment results in database"""
        async with self.database_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO quality_assessments (
                    assessment_id, submission_id, overall_score,
                    correctness_score, performance_score, security_score,
                    code_quality_score, documentation_score,
                    assessment_duration_ms, confidence_level
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                result.assessment_id, result.submission_id, result.overall_score,
                result.correctness_score.score, result.performance_score.score,
                result.security_score.score, result.code_quality_score.score,
                result.documentation_score.score, result.assessment_duration_ms,
                result.confidence_level
            )
            
    async def _emit_assessment_update(self, user_id: UUID, result: QualityAssessmentResult):
        """Emit assessment update via message bus"""
        if self.nats_client:
            message = {
                "submission_id": str(result.submission_id),
                "assessment_complete": True,
                "overall_score": result.overall_score,
                "dimension_scores": {
                    "correctness": result.correctness_score.score,
                    "performance": result.performance_score.score,
                    "security": result.security_score.score,
                    "code_quality": result.code_quality_score.score,
                    "documentation": result.documentation_score.score
                },
                "critical_issues": len(result.critical_issues),
                "timestamp": result.assessment_timestamp.isoformat()
            }
            await self.nats_client.publish(
                f"quality.updates.{user_id}",
                json.dumps(message).encode()
            )
            
    # Issue detection methods (simplified implementations)
    async def _detect_correctness_issues(self, code: str, language: str) -> List[CodeQualityIssue]:
        """Detect correctness-related issues"""
        issues = []
        
        # Check for undefined variables (simplified)
        if language == "python":
            # This would require AST analysis in a real implementation
            pass
            
        return issues
        
    async def _detect_performance_issues(self, code: str, language: str) -> List[CodeQualityIssue]:
        """Detect performance-related issues"""
        issues = []
        
        if code.count("for") > 10:
            issues.append(CodeQualityIssue(
                issue_id=uuid4(),
                dimension=QualityDimension.PERFORMANCE,
                severity="medium",
                description="Excessive use of loops",
                recommendation="Consider optimizing loop structures"
            ))
            
        return issues
        
    async def _detect_security_issues_list(self, code: str, language: str) -> List[CodeQualityIssue]:
        """Detect security-related issues"""
        issues = []
        
        for pattern in self.security_patterns:
            if re.search(pattern["pattern"], code, re.IGNORECASE):
                issues.append(CodeQualityIssue(
                    issue_id=uuid4(),
                    dimension=QualityDimension.SECURITY,
                    severity=pattern["severity"],
                    description=pattern["description"],
                    recommendation=pattern.get("recommendation", "Review security practices")
                ))
                
        return issues
        
    async def _detect_code_quality_issues(self, code: str, language: str) -> List[CodeQualityIssue]:
        """Detect code quality issues"""
        issues = []
        
        # Check for long lines
        for i, line in enumerate(code.split('\n'), 1):
            if len(line) > 120:
                issues.append(CodeQualityIssue(
                    issue_id=uuid4(),
                    dimension=QualityDimension.CODE_QUALITY,
                    severity="low",
                    description=f"Line {i} exceeds 120 characters",
                    line_number=i,
                    code_snippet=line,
                    recommendation="Break long lines for better readability"
                ))
                
        return issues
        
    async def _detect_documentation_issues(self, code: str, language: str) -> List[CodeQualityIssue]:
        """Detect documentation issues"""
        issues = []
        
        # Check comment density
        lines = code.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//')))
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines > 0 and (comment_lines / total_lines) < 0.1:
            issues.append(CodeQualityIssue(
                issue_id=uuid4(),
                dimension=QualityDimension.DOCUMENTATION,
                severity="medium",
                description="Low comment density",
                recommendation="Add more comments to explain complex logic"
            ))
            
        return issues
        
    # Configuration loading methods
    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load quality assessment rules"""
        return {
            "max_line_length": 120,
            "min_comment_ratio": 0.1,
            "max_function_complexity": 10,
            "naming_conventions": {
                "variables": "snake_case",
                "functions": "snake_case",
                "classes": "PascalCase"
            }
        }
        
    def _load_security_patterns(self) -> List[Dict[str, Any]]:
        """Load security vulnerability patterns"""
        return [
            {
                "name": "SQL Injection",
                "pattern": r"(SELECT|INSERT|UPDATE|DELETE).*\+",
                "description": "Potential SQL injection vulnerability",
                "severity": "high",
                "is_vulnerability": True,
                "recommendation": "Use parameterized queries"
            },
            {
                "name": "Eval Usage",
                "pattern": r"\beval\s*\(",
                "description": "Use of eval() function",
                "severity": "critical",
                "is_vulnerability": True,
                "recommendation": "Avoid eval() for security reasons"
            },
            {
                "name": "Hardcoded Password",
                "pattern": r"(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
                "description": "Hardcoded password detected",
                "severity": "high",
                "is_vulnerability": True,
                "recommendation": "Use environment variables for passwords"
            }
        ]
        
    def _load_performance_patterns(self) -> List[Dict[str, Any]]:
        """Load performance-related patterns"""
        return [
            {
                "name": "Nested Loops",
                "pattern": r"for.*for",
                "description": "Potential performance issue with nested loops",
                "severity": "medium"
            }
        ]
        
    # Additional helper methods (simplified)
    async def _check_input_validation(self, code: str, language: str) -> float:
        """Check input validation implementation"""
        score = 70.0
        if "validate" in code.lower() or "check" in code.lower():
            score += 20
        return min(100.0, score)
        
    async def _check_auth_patterns(self, code: str, language: str) -> float:
        """Check authentication/authorization patterns"""
        score = 75.0
        if "auth" in code.lower() or "login" in code.lower():
            score += 15
        return min(100.0, score)
        
    async def _check_data_exposure(self, code: str, language: str) -> float:
        """Check for data exposure risks"""
        score = 85.0
        if "print(" in code and "password" in code.lower():
            score -= 30
        return max(0.0, score)
        
    def _calculate_complexity_metrics(self, code: str) -> Dict[str, float]:
        """Calculate code complexity metrics"""
        lines = code.split('\n')
        return {
            "lines_of_code": len([line for line in lines if line.strip()]),
            "cyclomatic_complexity": min(20, lines.count("if") + lines.count("for") + lines.count("while")),
            "nesting_depth": max(0, max((line.count("{") - line.count("}")) for line in lines))
        }
        
    def _calculate_comment_density(self, code: str) -> float:
        """Calculate comment density"""
        lines = code.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//')))
        return (comment_lines / total_lines) if total_lines > 0 else 0.0
        
    def _calculate_docstring_coverage(self, code: str, language: str) -> float:
        """Calculate docstring coverage"""
        if language == "python":
            functions = [line for line in code.split('\n') if line.strip().startswith('def ')]
            docstrings = [line for line in code.split('\n') if '"""' in line]
            return min(1.0, len(docstrings) / max(len(functions), 1))
        return 0.5  # Default for other languages
        
    async def _check_naming_conventions(self, code: str, language: str) -> float:
        """Check naming conventions"""
        score = 80.0
        # Simplified naming check
        return score
        
    async def _check_code_structure(self, code: str, language: str) -> float:
        """Check code structure and organization"""
        score = 75.0
        if code.count('\n\n') > code.count('\n') * 0.1:
            score += 10  # Good separation
        return min(100.0, score)
        
    async def _check_code_smells(self, code: str) -> float:
        """Check for code smells"""
        score = 80.0
        if len(code.split('\n')) > 200:
            score -= 20  # File too large
        return max(0.0, score)
        
    async def _check_language_standards(self, code: str, language: str) -> float:
        """Check adherence to language-specific standards"""
        score = 85.0
        # Language-specific checks would go here
        return score
        
    async def _check_inline_comments(self, code: str) -> float:
        """Check for inline comments"""
        lines = code.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//')))
        total_lines = len([line for line in lines if line.strip()])
        return min(100.0, (comment_lines / total_lines) * 500) if total_lines > 0 else 0.0
        
    async def _check_docstrings(self, code: str, language: str) -> float:
        """Check for function/method docstrings"""
        if language == "python":
            functions = code.count('def ')
            docstrings = code.count('"""')
            return min(100.0, (docstrings / max(functions, 1)) * 200)
        return 60.0
        
    async def _check_external_documentation(self, code: str) -> float:
        """Check for external documentation references"""
        score = 70.0
        if "README" in code or "docs" in code.lower():
            score += 20
        return min(100.0, score)
        
    async def _check_naming_clarity(self, code: str) -> float:
        """Check for clear variable and function names"""
        score = 85.0
        # Simplified clarity check
        return score
        
    async def _generate_improvement_plan(self, correctness: DetailedScore, performance: DetailedScore,
                                       security: DetailedScore, code_quality: DetailedScore,
                                       documentation: DetailedScore) -> List[str]:
        """Generate detailed improvement plan"""
        plan = []
        
        if correctness.score < 70:
            plan.append("Focus on code correctness: Review logic and add error handling")
            
        if performance.score < 70:
            plan.append("Optimize performance: Review algorithms and reduce complexity")
            
        if security.score < 70:
            plan.append("Address security issues: Implement input validation and avoid unsafe functions")
            
        if code_quality.score < 70:
            plan.append("Improve code quality: Follow naming conventions and reduce code smells")
            
        if documentation.score < 70:
            plan.append("Enhance documentation: Add comments and improve code clarity")
            
        return plan


# Agent factory function
def create_quality_assessor_agent() -> QualityAssessorAgent:
    """Create and configure Quality Assessor Agent"""
    return QualityAssessorAgent()


# Export
__all__ = [
    "QualityAssessorAgent",
    "QualityAssessmentResult",
    "DetailedScore",
    "CodeQualityIssue",
    "QualityDimension",
    "QualityLevel",
    "create_quality_assessor_agent"
]