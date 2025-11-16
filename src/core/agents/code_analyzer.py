"""
Code Analyzer Agent with Code Context Graph (CCG)
Advanced code analysis for the Jaseci Learning Companion

This agent implements comprehensive code analysis using Code Context Graph (CCG)
for deep code understanding, relationship mapping, and learning insights.

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import ast
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import re
import os

import asyncpg
import redis.asyncio as redis
import nats
from pydantic import BaseModel, Field, validator
import networkx as nx

from ..registry import Agent, AgentMetadata, AgentType, AgentStatus, Priority, AgentTask


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Code Context Graph (CCG) Data Structures
class NodeType(str, Enum):
    """Types of nodes in the Code Context Graph"""
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    IMPORT = "import"
    STATEMENT = "statement"
    EXPRESSION = "expression"
    PARAMETER = "parameter"
    RETURN = "return"
    COMMENT = "comment"
    MODULE = "module"


class EdgeType(str, Enum):
    """Types of edges in the Code Context Graph"""
    CALLS = "calls"
    INHERITS = "inherits"
    DEFINES = "defines"
    USES = "uses"
    RETURNS = "returns"
    IMPORTS = "imports"
    CONTAINS = "contains"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"


class ComplexityMetric(str, Enum):
    """Code complexity metrics"""
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    COGNITIVE_COMPLEXITY = "cognitive_complexity"
    NESTING_DEPTH = "nesting_depth"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"
    LINES_OF_CODE = "lines_of_code"
    MAINTAINABILITY_INDEX = "maintainability_index"


@dataclass
class CCGNode:
    """Node in the Code Context Graph"""
    node_id: str
    node_type: NodeType
    name: str
    start_line: int
    end_line: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    complexity_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class CCGEdge:
    """Edge in the Code Context Graph"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class CodeContextGraph:
    """Code Context Graph representation"""
    
    def __init__(self, graph_id: UUID):
        self.graph_id = graph_id
        self.nodes: Dict[str, CCGNode] = {}
        self.edges: Dict[str, CCGEdge] = {}
        self.node_index: Dict[str, List[str]] = {}  # Index by node type
        self.edge_index: Dict[str, List[str]] = {}  # Index by edge type
        
    def add_node(self, node: CCGNode):
        """Add node to the graph"""
        self.nodes[node.node_id] = node
        
        # Update index
        if node.node_type not in self.node_index:
            self.node_index[node.node_type] = []
        self.node_index[node.node_type].append(node.node_id)
        
    def add_edge(self, edge: CCGEdge):
        """Add edge to the graph"""
        if edge.source_node_id in self.nodes and edge.target_node_id in self.nodes:
            self.edges[edge.edge_id] = edge
            
            # Update index
            if edge.edge_type not in self.edge_index:
                self.edge_index[edge.edge_type] = []
            self.edge_index[edge.edge_type].append(edge.edge_id)
            
    def get_nodes_by_type(self, node_type: NodeType) -> List[CCGNode]:
        """Get all nodes of a specific type"""
        return [self.nodes[node_id] for node_id in self.node_index.get(node_type, [])]
        
    def get_edges_by_type(self, edge_type: EdgeType) -> List[CCGEdge]:
        """Get all edges of a specific type"""
        return [self.edges[edge_id] for edge_id in self.edge_index.get(edge_type, [])]
        
    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get all nodes that this node depends on"""
        dependencies = set()
        for edge in self.edges.values():
            if edge.source_node_id == node_id and edge.edge_type in [EdgeType.USES, EdgeType.DEPENDS_ON]:
                dependencies.add(edge.target_node_id)
        return dependencies
        
    def get_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node"""
        dependents = set()
        for edge in self.edges.values():
            if edge.target_node_id == node_id and edge.edge_type in [EdgeType.USES, EdgeType.DEPENDS_ON]:
                dependents.add(edge.source_node_id)
        return dependents
        
    def calculate_complexity(self) -> Dict[str, float]:
        """Calculate overall graph complexity"""
        complexity = {}
        
        # Cyclomatic complexity (simplified)
        decision_points = len(self.get_edges_by_type(EdgeType.CALLS))
        complexity[ComplexityMetric.CYCLOMATIC_COMPLEXITY] = decision_points + 1
        
        # Fan out (functions that call many others)
        function_nodes = self.get_nodes_by_type(NodeType.FUNCTION)
        if function_nodes:
            fan_out_scores = []
            for func in function_nodes:
                dependencies = len(self.get_dependencies(func.node_id))
                fan_out_scores.append(dependencies)
            complexity[ComplexityMetric.FAN_OUT] = sum(fan_out_scores) / len(fan_out_scores)
        
        # Nesting depth
        nesting_depth = self._calculate_max_nesting_depth()
        complexity[ComplexityMetric.NESTING_DEPTH] = nesting_depth
        
        return complexity
        
    def _calculate_max_nesting_depth(self) -> float:
        """Calculate maximum nesting depth"""
        max_depth = 0
        for node in self.nodes.values():
            if node.properties.get('nesting_level', 0) > max_depth:
                max_depth = node.properties.get('nesting_level', 0)
        return max_depth
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization"""
        return {
            "graph_id": str(self.graph_id),
            "nodes": {nid: {
                "node_id": node.node_id,
                "node_type": node.node_type.value,
                "name": node.name,
                "start_line": node.start_line,
                "end_line": node.end_line,
                "content": node.content,
                "metadata": node.metadata,
                "properties": node.properties,
                "complexity_scores": node.complexity_scores
            } for nid, node in self.nodes.items()},
            "edges": {eid: {
                "edge_id": edge.edge_id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "edge_type": edge.edge_type.value,
                "weight": edge.weight,
                "properties": edge.properties
            } for eid, edge in self.edges.items()},
            "statistics": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "node_types": {nt.value: len(node_ids) for nt, node_ids in self.node_index.items()},
                "edge_types": {et.value: len(edge_ids) for et, edge_ids in self.edge_index.items()}
            }
        }


class CodeAnalysisResult(BaseModel):
    """Result of code analysis"""
    submission_id: UUID
    graph_id: UUID
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Code metrics
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Complexity metrics
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 0.0
    
    # Graph metrics
    total_nodes: int = 0
    total_edges: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    
    # Code quality indicators
    code_smells: List[str] = Field(default_factory=list)
    security_issues: List[str] = Field(default_factory=list)
    performance_concerns: List[str] = Field(default_factory=list)
    best_practices_violations: List[str] = Field(default_factory=list)
    
    # Learning insights
    concepts_demonstrated: List[str] = Field(default_factory=list)
    difficulty_level: str = "intermediate"
    estimated_learning_time_minutes: int = 30
    
    # Recommendations
    improvement_suggestions: List[str] = Field(default_factory=list)
    next_concepts_to_learn: List[str] = Field(default_factory=list)


class CodeSubmission(BaseModel):
    """Code submission for analysis"""
    submission_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    code: str
    language: str = Field(default="jac", regex="^(jac|python|javascript|typescript)$")
    lesson_id: Optional[UUID] = None
    exercise_id: Optional[UUID] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CodeAnalyzerAgent(Agent):
    """Code Analyzer Agent with CCG implementation"""
    
    def __init__(self):
        super().__init__(
            agent_id=uuid4(),
            agent_type=AgentType.CODE_ANALYZER,
            name="Code Context Graph Analyzer",
            version="2.0.0-enterprise"
        )
        self.redis_client = None
        self.database_pool = None
        self.nats_client = None
        self.analysis_cache: Dict[str, CodeContextGraph] = {}
        
        # Language-specific parsers
        self.parsers = {
            "jac": self._parse_jac_code,
            "python": self._parse_python_code,
            "javascript": self._parse_javascript_code,
            "typescript": self._parse_typescript_code
        }
        
        # Code quality rules
        self.quality_rules = self._load_quality_rules()
        
    async def initialize(self) -> bool:
        """Initialize the Code Analyzer Agent"""
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
            await self.register_capability("analyze_code")
            await self.register_capability("build_context_graph")
            await self.register_capability("calculate_complexity")
            await self.register_capability("detect_code_smells")
            await self.register_capability("generate_learning_insights")
            await self.register_capability("extract_concepts")
            
            # Subscribe to NATS subjects
            await self.nats_client.subscribe("code.submissions.*", self._handle_code_submission)
            await self.nats_client.subscribe("analysis.requests.*", self._handle_analysis_request)
            
            logger.info("Code Analyzer Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Code Analyzer Agent: {e}")
            return False
            
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process code analysis tasks"""
        try:
            task_type = task.task_type
            
            if task_type == "analyze_code":
                return await self._analyze_code(task.payload)
            elif task_type == "build_graph":
                return await self._build_context_graph(task.payload)
            elif task_type == "calculate_complexity":
                return await self._calculate_complexity_metrics(task.payload)
            elif task_type == "detect_issues":
                return await self._detect_code_issues(task.payload)
            elif task_type == "extract_concepts":
                return await self._extract_learning_concepts(task.payload)
            elif task_type == "get_graph":
                return await self._get_context_graph(task.payload)
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
                "supported_languages": list(self.parsers.keys()),
                "analysis_cache_size": len(self.analysis_cache),
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
    async def _handle_code_submission(self, msg):
        """Handle code submission events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._analyze_code(data)
        except Exception as e:
            logger.error(f"Error handling code submission: {e}")
            
    async def _handle_analysis_request(self, msg):
        """Handle analysis request events from NATS"""
        try:
            data = json.loads(msg.data.decode())
            await self._analyze_code(data)
        except Exception as e:
            logger.error(f"Error handling analysis request: {e}")
            
    # Main processing methods
    async def _analyze_code(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code and generate comprehensive report"""
        try:
            # Parse code submission
            submission = CodeSubmission(**payload)
            
            # Build Code Context Graph
            graph = await self._build_context_graph(submission)
            
            # Calculate metrics
            metrics = self._calculate_code_metrics(submission.code, graph)
            
            # Detect issues
            issues = await self._detect_code_issues(submission.code, graph)
            
            # Extract learning concepts
            concepts = await self._extract_learning_concepts(submission.code, graph)
            
            # Generate analysis result
            analysis_result = CodeAnalysisResult(
                submission_id=submission.submission_id,
                graph_id=graph.graph_id,
                total_lines=metrics["total_lines"],
                code_lines=metrics["code_lines"],
                comment_lines=metrics["comment_lines"],
                blank_lines=metrics["blank_lines"],
                cyclomatic_complexity=metrics["cyclomatic_complexity"],
                cognitive_complexity=metrics["cognitive_complexity"],
                maintainability_index=metrics["maintainability_index"],
                total_nodes=len(graph.nodes),
                total_edges=len(graph.edges),
                function_count=len(graph.get_nodes_by_type(NodeType.FUNCTION)),
                class_count=len(graph.get_nodes_by_type(NodeType.CLASS)),
                import_count=len(graph.get_nodes_by_type(NodeType.IMPORT)),
                code_smells=issues["code_smells"],
                security_issues=issues["security_issues"],
                performance_concerns=issues["performance_concerns"],
                best_practices_violations=issues["best_practices"],
                concepts_demonstrated=concepts,
                difficulty_level=self._assess_difficulty_level(metrics, graph),
                improvement_suggestions=self._generate_improvement_suggestions(metrics, issues),
                next_concepts_to_learn=self._recommend_next_concepts(concepts, issues)
            )
            
            # Store results
            await self._store_analysis_results(analysis_result, graph)
            
            # Emit real-time update
            await self._emit_analysis_update(submission.user_id, analysis_result)
            
            logger.info(f"Analyzed code for submission {submission.submission_id}")
            
            return {
                "status": "success",
                "analysis_result": analysis_result.dict(),
                "graph_id": str(graph.graph_id)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _build_context_graph(self, submission: CodeSubmission) -> CodeContextGraph:
        """Build Code Context Graph from code submission"""
        try:
            # Create new graph
            graph = CodeContextGraph(graph_id=uuid4())
            
            # Get appropriate parser
            parser = self.parsers.get(submission.language, self.parsers["jac"])
            
            # Parse code and build graph
            await parser(graph, submission.code, submission.submission_id)
            
            # Cache the graph
            self.analysis_cache[str(graph.graph_id)] = graph
            
            # Store graph in database
            await self._store_context_graph(graph)
            
            return graph
            
        except Exception as e:
            logger.error(f"Error building context graph: {e}")
            raise
            
    async def _parse_jac_code(self, graph: CodeContextGraph, code: str, submission_id: UUID):
        """Parse Jaseci-specific code structure"""
        # Jaseci uses graph-based programming
        lines = code.split('\n')
        current_function = None
        nesting_level = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('//') or stripped.startswith('#'):
                if stripped.startswith('//') or stripped.startswith('#'):
                    # Add comment node
                    comment_node = CCGNode(
                        node_id=f"comment_{i}",
                        node_type=NodeType.COMMENT,
                        name=f"comment_{i}",
                        start_line=i,
                        end_line=i,
                        content=stripped
                    )
                    graph.add_node(comment_node)
                continue
                
            # Parse function definitions (simplified)
            if 'def ' in stripped or 'walker ' in stripped:
                func_name = self._extract_function_name(stripped)
                func_node = CCGNode(
                    node_id=f"function_{i}",
                    node_type=NodeType.FUNCTION,
                    name=func_name,
                    start_line=i,
                    end_line=i,
                    content=stripped,
                    properties={"language": "jac", "nesting_level": nesting_level}
                )
                graph.add_node(func_node)
                current_function = func_node.node_id
                
            # Parse variable assignments
            if '=' in stripped and not stripped.startswith('def '):
                var_name = stripped.split('=')[0].strip()
                var_node = CCGNode(
                    node_id=f"variable_{i}",
                    node_type=NodeType.VARIABLE,
                    name=var_name,
                    start_line=i,
                    end_line=i,
                    content=stripped
                )
                graph.add_node(var_node)
                
                # Add edge from function to variable (defines)
                if current_function:
                    edge = CCGEdge(
                        edge_id=f"edge_{current_function}_{var_node.node_id}",
                        source_node_id=current_function,
                        target_node_id=var_node.node_id,
                        edge_type=EdgeType.DEFINES
                    )
                    graph.add_edge(edge)
                    
            # Parse function calls
            if '(' in stripped and ')' in stripped and not stripped.startswith('def '):
                call_target = stripped.split('(')[0].strip()
                if call_target:
                    call_node = CCGNode(
                        node_id=f"call_{i}",
                        node_type=NodeType.STATEMENT,
                        name=f"call_{call_target}",
                        start_line=i,
                        end_line=i,
                        content=stripped
                    )
                    graph.add_node(call_node)
                    
                    # Add edge from function to call (calls)
                    if current_function:
                        edge = CCGEdge(
                            edge_id=f"edge_{current_function}_{call_node.node_id}",
                            source_node_id=current_function,
                            target_node_id=call_node.node_id,
                            edge_type=EdgeType.CALLS
                        )
                        graph.add_edge(edge)
                        
            # Track nesting
            nesting_level = max(0, nesting_level + stripped.count('{') - stripped.count('}'))
            
        # Add module root node
        module_node = CCGNode(
            node_id=f"module_{submission_id}",
            node_type=NodeType.MODULE,
            name="jac_module",
            start_line=1,
            end_line=len(lines),
            content=code
        )
        graph.add_node(module_node)
        
    async def _parse_python_code(self, graph: CodeContextGraph, code: str, submission_id: UUID):
        """Parse Python code using AST"""
        try:
            tree = ast.parse(code)
            module_node = CCGNode(
                node_id=f"module_{submission_id}",
                node_type=NodeType.MODULE,
                name="python_module",
                start_line=1,
                end_line=len(code.split('\n')),
                content=code
            )
            graph.add_node(module_node)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_node = CCGNode(
                        node_id=f"function_{node.lineno}",
                        node_type=NodeType.FUNCTION,
                        name=node.name,
                        start_line=node.lineno,
                        end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        content=ast.get_source_segment(code, node)
                    )
                    graph.add_node(func_node)
                    
                elif isinstance(node, ast.ClassDef):
                    class_node = CCGNode(
                        node_id=f"class_{node.lineno}",
                        node_type=NodeType.CLASS,
                        name=node.name,
                        start_line=node.lineno,
                        end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        content=ast.get_source_segment(code, node)
                    )
                    graph.add_node(class_node)
                    
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_node = CCGNode(
                                node_id=f"variable_{node.lineno}_{target.id}",
                                node_type=NodeType.VARIABLE,
                                name=target.id,
                                start_line=node.lineno,
                                end_line=node.lineno,
                                content=ast.get_source_segment(code, node)
                            )
                            graph.add_node(var_node)
                            
        except SyntaxError as e:
            logger.error(f"Python syntax error: {e}")
            
    async def _parse_javascript_code(self, graph: CodeContextGraph, code: str, submission_id: UUID):
        """Parse JavaScript/TypeScript code (simplified)"""
        # Simplified JavaScript parsing - could be enhanced with proper AST parser
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Function declarations
            if re.search(r'function\s+\w+', stripped):
                match = re.search(r'function\s+(\w+)', stripped)
                if match:
                    func_name = match.group(1)
                    func_node = CCGNode(
                        node_id=f"function_{i}",
                        node_type=NodeType.FUNCTION,
                        name=func_name,
                        start_line=i,
                        end_line=i,
                        content=stripped
                    )
                    graph.add_node(func_node)
                    
            # Arrow functions
            elif re.search(r'const\s+\w+\s*=', stripped):
                match = re.search(r'const\s+(\w+)', stripped)
                if match:
                    func_name = match.group(1)
                    func_node = CCGNode(
                        node_id=f"arrow_function_{i}",
                        node_type=NodeType.FUNCTION,
                        name=func_name,
                        start_line=i,
                        end_line=i,
                        content=stripped
                    )
                    graph.add_node(func_node)
                    
            # Variable declarations
            elif re.search(r'(const|let|var)\s+\w+', stripped):
                match = re.search(r'(const|let|var)\s+(\w+)', stripped)
                if match:
                    var_name = match.group(2)
                    var_node = CCGNode(
                        node_id=f"variable_{i}",
                        node_type=NodeType.VARIABLE,
                        name=var_name,
                        start_line=i,
                        end_line=i,
                        content=stripped
                    )
                    graph.add_node(var_node)
                    
    async def _parse_typescript_code(self, graph: CodeContextGraph, code: str, submission_id: UUID):
        """Parse TypeScript code - similar to JavaScript but with type annotations"""
        # Use the same parsing as JavaScript for now
        await self._parse_javascript_code(graph, code, submission_id)
        
    def _calculate_code_metrics(self, code: str, graph: CodeContextGraph) -> Dict[str, Any]:
        """Calculate comprehensive code metrics"""
        lines = code.split('\n')
        
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith(('//', '#', '/*'))])
        blank_lines = total_lines - code_lines
        
        # Calculate cyclomatic complexity
        cyclomatic_complexity = 1  # Base complexity
        for node in graph.nodes.values():
            if node.node_type == NodeType.FUNCTION:
                # Count decision points in function
                decision_points = len([edge for edge in graph.edges.values() 
                                     if edge.source_node_id == node.node_id 
                                     and edge.edge_type in [EdgeType.CALLS]])
                cyclomatic_complexity += decision_points
                
        # Calculate cognitive complexity (simplified)
        nesting_level = 0
        cognitive_complexity = 0
        
        for line in lines:
            nesting_level = max(0, nesting_level + line.count('{') - line.count('}'))
            if any(keyword in line for keyword in ['if', 'for', 'while', 'case']):
                cognitive_complexity += nesting_level + 1
                
        # Calculate maintainability index (simplified Halstead metric)
        operators = len(re.findall(r'[+\-*/%=<>!&|^~]', code))
        operands = len(re.findall(r'\b\w+\b', code))
        maintainability_index = max(0, 171 - 5.2 * math.log(operators + 1) - 0.23 * cognitive_complexity)
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "cyclomatic_complexity": cyclomatic_complexity,
            "cognitive_complexity": cognitive_complexity,
            "maintainability_index": maintainability_index,
            "operators": operators,
            "operands": operands
        }
        
    async def _detect_code_issues(self, code: str, graph: CodeContextGraph) -> Dict[str, List[str]]:
        """Detect code quality issues"""
        issues = {
            "code_smells": [],
            "security_issues": [],
            "performance_concerns": [],
            "best_practices": []
        }
        
        # Check for code smells
        if len(graph.nodes) > 50:
            issues["code_smells"].append("Large file with too many elements")
            
        # Check for security issues
        if "eval(" in code:
            issues["security_issues"].append("Use of eval() function - security risk")
        if "exec(" in code:
            issues["security_issues"].append("Use of exec() function - security risk")
            
        # Check for performance issues
        if code.count("for") > code.count("while"):
            issues["performance_concerns"].append("Consider using more efficient iteration patterns")
            
        # Check for best practices
        if not graph.get_nodes_by_type(NodeType.COMMENT):
            issues["best_practices"].append("Consider adding code comments for better readability")
            
        # Check function complexity
        for func in graph.get_nodes_by_type(NodeType.FUNCTION):
            func_edges = len([edge for edge in graph.edges.values() 
                            if edge.source_node_id == func.node_id])
            if func_edges > 10:
                issues["code_smells"].append(f"Function '{func.name}' has high complexity")
                
        return issues
        
    async def _extract_learning_concepts(self, code: str, graph: CodeContextGraph) -> List[str]:
        """Extract learning concepts from code"""
        concepts = []
        
        # Check for specific programming concepts
        if graph.get_nodes_by_type(NodeType.FUNCTION):
            concepts.append("Function Definition")
            
        if graph.get_nodes_by_type(NodeType.CLASS):
            concepts.append("Object-Oriented Programming")
            
        if any(edge.edge_type == EdgeType.CALLS for edge in graph.edges.values()):
            concepts.append("Function Calls")
            
        if graph.get_nodes_by_type(NodeType.IMPORT):
            concepts.append("Module Imports")
            
        # Check for Jaseci-specific concepts
        if "walker" in code:
            concepts.append("Jaseci Walkers")
            
        if "graph" in code and "{" in code:
            concepts.append("Graph Programming")
            
        if "node" in code and "edges" in code:
            concepts.append("Node and Edge Relationships")
            
        return list(set(concepts))
        
    async def _store_analysis_results(self, result: CodeAnalysisResult, graph: CodeContextGraph):
        """Store analysis results in database"""
        async with self.database_pool.acquire() as conn:
            # Store analysis result
            await conn.execute("""
                INSERT INTO code_analysis_results (
                    submission_id, analysis_timestamp, total_lines, code_lines,
                    cyclomatic_complexity, cognitive_complexity, total_nodes,
                    total_edges, concepts_demonstrated, difficulty_level
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                result.submission_id, result.analysis_timestamp, result.total_lines,
                result.code_lines, result.cyclomatic_complexity, result.cognitive_complexity,
                result.total_nodes, result.total_edges, result.concepts_demonstrated,
                result.difficulty_level
            )
            
    async def _store_context_graph(self, graph: CodeContextGraph):
        """Store context graph in database"""
        async with self.database_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO code_context_graphs (
                    graph_id, graph_type, language, nodes_data, edges_data
                ) VALUES ($1, 'analysis', 'jac', $2, $3)
            """,
                graph.graph_id,
                json.dumps({nid: node.__dict__ for nid, node in graph.nodes.items()}),
                json.dumps({eid: edge.__dict__ for eid, edge in graph.edges.items()})
            )
            
    async def _emit_analysis_update(self, user_id: UUID, result: CodeAnalysisResult):
        """Emit analysis update via message bus"""
        if self.nats_client:
            message = {
                "submission_id": str(result.submission_id),
                "analysis_complete": True,
                "complexity_score": result.cyclomatic_complexity,
                "concepts_found": result.concepts_demonstrated,
                "difficulty_level": result.difficulty_level,
                "timestamp": result.analysis_timestamp.isoformat()
            }
            await self.nats_client.publish(
                f"analysis.updates.{user_id}",
                json.dumps(message).encode()
            )
            
    def _assess_difficulty_level(self, metrics: Dict[str, Any], graph: CodeContextGraph) -> str:
        """Assess difficulty level based on metrics"""
        complexity_score = metrics["cyclomatic_complexity"] + metrics["cognitive_complexity"]
        
        if complexity_score > 20:
            return "advanced"
        elif complexity_score > 10:
            return "intermediate"
        elif complexity_score > 5:
            return "beginner"
        else:
            return "basic"
            
    def _generate_improvement_suggestions(self, metrics: Dict[str, Any], issues: Dict[str, List[str]]) -> List[str]:
        """Generate code improvement suggestions"""
        suggestions = []
        
        if metrics["cognitive_complexity"] > 10:
            suggestions.append("Consider breaking down complex functions into smaller ones")
            
        if metrics["comment_lines"] / max(metrics["code_lines"], 1) < 0.1:
            suggestions.append("Add more comments to explain complex logic")
            
        if "security_issues" in issues and issues["security_issues"]:
            suggestions.extend(["Review security practices and avoid dangerous functions"])
            
        return suggestions
        
    def _recommend_next_concepts(self, concepts: List[str], issues: Dict[str, List[str]]) -> List[str]:
        """Recommend next concepts to learn"""
        recommendations = []
        
        if "Function Definition" in concepts:
            recommendations.append("Higher-Order Functions")
            
        if "Graph Programming" in concepts:
            recommendations.append("Graph Traversal Algorithms")
            
        if "Object-Oriented Programming" in concepts:
            recommendations.append("Design Patterns")
            
        return recommendations
        
    def _extract_function_name(self, line: str) -> str:
        """Extract function name from a line of code"""
        # Simple function name extraction for Jaseci
        if 'def ' in line:
            return line.split('def ')[1].split('(')[0].strip()
        elif 'walker ' in line:
            return line.split('walker ')[1].split('(')[0].strip()
        return "unknown_function"
        
    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load code quality rules and patterns"""
        return {
            "max_function_complexity": 10,
            "max_file_size": 500,
            "required_comment_ratio": 0.1,
            "security_keywords": ["eval", "exec", "os.system", "subprocess"],
            "performance_keywords": ["while", "for", "nested_loops"]
        }
        
    async def _get_context_graph(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get stored context graph"""
        try:
            graph_id = UUID(payload.get("graph_id"))
            
            # Check cache first
            if str(graph_id) in self.analysis_cache:
                graph = self.analysis_cache[str(graph_id)]
            else:
                # Load from database
                async with self.database_pool.acquire() as conn:
                    graph_data = await conn.fetchrow("""
                        SELECT * FROM code_context_graphs WHERE graph_id = $1
                    """, graph_id)
                    
                if not graph_data:
                    return {"status": "error", "message": "Graph not found"}
                    
                # Rebuild graph from stored data
                graph = self._rebuild_graph_from_data(graph_data)
                
            return {
                "status": "success",
                "graph": graph.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting context graph: {e}")
            return {"status": "error", "message": str(e)}
            
    def _rebuild_graph_from_data(self, graph_data) -> CodeContextGraph:
        """Rebuild graph from database data"""
        graph = CodeContextGraph(graph_data['graph_id'])
        
        # Rebuild nodes
        nodes_data = json.loads(graph_data['nodes_data'])
        for node_id, node_dict in nodes_data.items():
            node = CCGNode(
                node_id=node_dict['node_id'],
                node_type=NodeType(node_dict['node_type']),
                name=node_dict['name'],
                start_line=node_dict['start_line'],
                end_line=node_dict['end_line'],
                content=node_dict['content'],
                metadata=node_dict.get('metadata', {}),
                properties=node_dict.get('properties', {}),
                complexity_scores=node_dict.get('complexity_scores', {})
            )
            graph.add_node(node)
            
        # Rebuild edges
        edges_data = json.loads(graph_data['edges_data'])
        for edge_id, edge_dict in edges_data.items():
            edge = CCGEdge(
                edge_id=edge_dict['edge_id'],
                source_node_id=edge_dict['source_node_id'],
                target_node_id=edge_dict['target_node_id'],
                edge_type=EdgeType(edge_dict['edge_type']),
                weight=edge_dict.get('weight', 1.0),
                properties=edge_dict.get('properties', {})
            )
            graph.add_edge(edge)
            
        return graph


# Agent factory function
def create_code_analyzer_agent() -> CodeAnalyzerAgent:
    """Create and configure Code Analyzer Agent"""
    return CodeAnalyzerAgent()


# Export
__all__ = [
    "CodeAnalyzerAgent",
    "CodeContextGraph",
    "CCGNode",
    "CCGEdge",
    "CodeAnalysisResult",
    "NodeType",
    "EdgeType",
    "create_code_analyzer_agent"
]