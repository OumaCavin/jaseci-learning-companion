"""
Jaseci AST Parser for OSP Graph Generation

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Jaseci Abstract Syntax Tree (AST) parser that converts Jaseci code
into OSP (Object-Subject-Predicate) graph structures for the
Jaseci Learning Companion system.
"""

import ast
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, deque
import json

from services.core.osp_graph_service.models.osp_models import (
    OSPNode, OSPRelationship, OSPGraph, OSPAnalysis,
    JaseciCodeElement, CodeComplexityMetrics, NodeType, RelationshipType,
    JaseciNodeType
)

logger = logging.getLogger(__name__)


@dataclass
class JaseciASTNode:
    """Internal representation of Jaseci AST node"""
    node_type: str
    name: str
    value: Any
    properties: Dict[str, Any]
    location: Dict[str, int]
    children: List['JaseciASTNode']
    parent: Optional['JaseciASTNode'] = None


class JaseciASTParser:
    """Jaseci AST Parser for OSP graph generation"""
    
    def __init__(self):
        """Initialize the Jaseci AST parser"""
        self.node_counter = 0
        self.relationship_counter = 0
        self.jaseci_keywords = {
            'walker', 'node', 'edge', 'action', 'can',
            'with', 'break', 'continue', 'if', 'elif', 'else',
            'for', 'while', 'try', 'except', 'finally',
            'return', 'yield', 'import', 'from', 'as',
            'class', 'def', 'global', 'nonlocal',
            'assert', 'del', 'pass', 'raise', 'lambda'
        }
        
        self.jaseci_special_forms = {
            'spawn', 'visit', 'take', 'here', 'root', 'out',
            'incoming', 'outgoing', 'local', 'global',
            'report', 'ignore_errors', 'stdin', 'stdout'
        }
        
        self.node_id_mapping = {}
        self.visited_nodes = set()
    
    async def parse_and_generate_osp(
        self, 
        code: str, 
        filename: Optional[str] = None, 
        project_id: Optional[str] = None
    ) -> OSPAnalysis:
        """Parse Jaseci code and generate OSP graph"""
        try:
            logger.info(f"🧩 Starting Jaseci AST parsing for {filename or 'anonymous'}")
            
            # Reset state
            self.node_counter = 0
            self.relationship_counter = 0
            self.node_id_mapping = {}
            self.visited_nodes = set()
            
            # Parse the Jaseci code
            ast_tree = self._parse_jaseci_code(code, filename)
            
            # Generate OSP nodes and relationships
            nodes, relationships = await self._generate_osp_elements(ast_tree, project_id)
            
            # Create OSP graph
            osp_graph = OSPGraph(
                id=f"graph_{project_id}_{filename}",
                name=f"Jaseci Code Graph - {filename or 'Anonymous'}",
                project_id=project_id,
                nodes=[node.to_dict() for node in nodes],
                relationships=[rel.to_dict() for rel in relationships],
                metadata={
                    "source_file": filename,
                    "code_lines": len(code.splitlines()),
                    "parsing_timestamp": ast_tree.created_at.isoformat() if hasattr(ast_tree, 'created_at') else None,
                    "parser_version": "1.0.0"
                }
            )
            
            # Perform complexity analysis
            complexity_metrics = self._analyze_complexity(ast_tree)
            
            # Generate insights and recommendations
            insights = self._generate_insights(complexity_metrics, nodes, relationships)
            recommendations = self._generate_recommendations(complexity_metrics, nodes, relationships)
            
            # Create analysis result
            analysis = OSPAnalysis(
                analysis_type="jaseci_code_analysis",
                project_id=project_id or "default",
                results={
                    "osp_graph": osp_graph.to_dict(),
                    "complexity_metrics": complexity_metrics.dict(),
                    "element_counts": {
                        "nodes": len(nodes),
                        "relationships": len(relationships),
                        "node_types": len(set(node.node_type for node in nodes)),
                        "relationship_types": len(set(rel.relationship_type for rel in relationships))
                    }
                },
                metrics={
                    "nodes_analyzed": len(nodes),
                    "relationships_analyzed": len(relationships),
                    "code_lines": len(code.splitlines()),
                    "parsing_time": 0.0  # Will be set by caller
                },
                insights=insights,
                recommendations=recommendations
            )
            
            logger.info(f"✅ Successfully parsed Jaseci code: {len(nodes)} nodes, {len(relationships)} relationships")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error parsing Jaseci code: {str(e)}")
            raise
    
    def _parse_jaseci_code(self, code: str, filename: Optional[str]) -> JaseciASTNode:
        """Parse Jaseci code into AST structure"""
        try:
            # First, try standard Python AST parsing
            tree = ast.parse(code, filename=filename or "anonymous.jac")
            return self._convert_ast_to_jaseci_ast(tree, filename)
        except SyntaxError as e:
            # If standard parsing fails, try Jaseci-specific parsing
            logger.warning(f"Standard AST parsing failed, trying Jaseci-specific parsing: {e}")
            return self._parse_jaseci_specific(code, filename)
    
    def _convert_ast_to_jaseci_ast(self, python_ast: ast.AST, filename: Optional[str]) -> JaseciASTNode:
        """Convert Python AST to Jaseci AST structure"""
        def visit_node(node: ast.AST, parent: Optional[JaseciASTNode] = None) -> JaseciASTNode:
            node_type = type(node).__name__
            name = getattr(node, 'name', None) or f"unnamed_{node_type}"
            
            # Extract location information
            location = {}
            if hasattr(node, 'lineno'):
                location['line'] = node.lineno
            if hasattr(node, 'col_offset'):
                location['column'] = node.col_offset
            
            # Create Jaseci-specific node type
            jaseci_node_type = self._map_python_to_jaseci_node_type(node_type)
            
            # Extract properties
            properties = self._extract_node_properties(node)
            
            # Create the Jaseci AST node
            jaseci_node = JaseciASTNode(
                node_type=jaseci_node_type,
                name=name,
                value=getattr(node, 'value', None),
                properties=properties,
                location=location,
                children=[],
                parent=parent
            )
            
            # Process child nodes
            for child in ast.iter_child_nodes(node):
                child_node = visit_node(child, jaseci_node)
                jaseci_node.children.append(child_node)
            
            return jaseci_node
        
        # Visit the root node
        root_node = visit_node(python_ast)
        root_node.name = f"program_{filename or 'anonymous'}"
        
        return root_node
    
    def _map_python_to_jaseci_node_type(self, python_type: str) -> str:
        """Map Python AST node types to Jaseci node types"""
        mapping = {
            'FunctionDef': 'walker',
            'AsyncFunctionDef': 'walker',
            'ClassDef': 'node',
            'Import': 'import',
            'ImportFrom': 'import',
            'Assign': 'variable',
            'AugAssign': 'variable',
            'AnnAssign': 'variable',
            'For': 'block',
            'AsyncFor': 'block',
            'While': 'block',
            'If': 'block',
            'Try': 'block',
            'With': 'block',
            'Return': 'statement',
            'Yield': 'statement',
            'Raise': 'statement',
            'Break': 'statement',
            'Continue': 'statement',
            'Pass': 'statement',
            'Assert': 'statement',
            'Delete': 'statement',
            'Expr': 'expression',
            'Call': 'action',
            'Attribute': 'expression',
            'Subscript': 'expression',
            'BinOp': 'expression',
            'UnaryOp': 'expression',
            'BoolOp': 'expression',
            'Compare': 'expression',
            'Lambda': 'expression',
            'List': 'collection',
            'Tuple': 'collection',
            'Dict': 'collection',
            'Set': 'collection',
            'Name': 'identifier',
            'Constant': 'literal',
            'Str': 'literal',
            'Num': 'literal',
            'ListComp': 'comprehension',
            'SetComp': 'comprehension',
            'DictComp': 'comprehension',
            'GeneratorExp': 'comprehension',
        }
        
        return mapping.get(python_type, 'unknown')
    
    def _extract_node_properties(self, node: ast.AST) -> Dict[str, Any]:
        """Extract properties from AST node"""
        properties = {}
        
        # Common properties
        if hasattr(node, 'lineno'):
            properties['line'] = node.lineno
        if hasattr(node, 'col_offset'):
            properties['column'] = node.col_offset
        if hasattr(node, 'name'):
            properties['function_name'] = node.name
        
        # Function-specific properties
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            properties['args_count'] = len(node.args.args)
            properties['has_varargs'] = bool(node.args.vararg)
            properties['has_kwargs'] = bool(node.args.kwonlyargs)
            properties['is_async'] = isinstance(node, ast.AsyncFunctionDef)
            properties['decorators_count'] = len(node.decorator_list)
        
        # Class-specific properties
        if isinstance(node, ast.ClassDef):
            properties['bases_count'] = len(node.bases)
            properties['methods_count'] = len([n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
            properties['has_metaclass'] = bool(node.keywords)
        
        # Import-specific properties
        if isinstance(node, ast.Import):
            properties['names_count'] = len(node.names)
        if isinstance(node, ast.ImportFrom):
            properties['module'] = node.module
            properties['names_count'] = len(node.names)
        
        # Loop-specific properties
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            properties['has_else'] = bool(node.orelse)
        
        # If-specific properties
        if isinstance(node, ast.If):
            properties['has_else'] = bool(node.orelse)
            properties['has_elif'] = len(node.orelse) > 0 and isinstance(node.orelse[0], ast.If)
        
        return properties
    
    def _parse_jaseci_specific(self, code: str, filename: Optional[str]) -> JaseciASTNode:
        """Parse Jaseci-specific syntax that might not be valid Python"""
        lines = code.splitlines()
        
        # Create program node
        program_node = JaseciASTNode(
            node_type='program',
            name=f"program_{filename or 'anonymous'}",
            value=None,
            properties={'total_lines': len(lines)},
            location={'line': 1, 'column': 0},
            children=[]
        )
        
        # Parse each line
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse Jaseci-specific constructs
            element = self._parse_jaseci_line(line, i)
            if element:
                program_node.children.append(element)
        
        return program_node
    
    def _parse_jaseci_line(self, line: str, line_number: int) -> Optional[JaseciASTNode]:
        """Parse a single Jaseci line"""
        # Remove comments
        if '#' in line:
            line = line.split('#')[0].strip()
        
        if not line:
            return None
        
        # Detect Jaseci constructs
        if line.startswith('walker '):
            return self._parse_walker_declaration(line, line_number)
        elif line.startswith('node '):
            return self._parse_node_declaration(line, line_number)
        elif line.startswith('edge '):
            return self._parse_edge_declaration(line, line_number)
        elif line.startswith('can '):
            return self._parse_can_action(line, line_number)
        elif 'spawn' in line:
            return self._parse_spawn_statement(line, line_number)
        elif 'visit' in line:
            return self._parse_visit_statement(line, line_number)
        elif 'take' in line:
            return self._parse_take_statement(line, line_number)
        elif 'report' in line:
            return self._parse_report_statement(line, line_number)
        else:
            return self._parse_general_statement(line, line_number)
    
    def _parse_walker_declaration(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse walker declaration"""
        match = re.match(r'walker\s+(\w+)', line)
        if match:
            walker_name = match.group(1)
            return JaseciASTNode(
                node_type='walker',
                name=walker_name,
                value=line,
                properties={'declaration_type': 'walker'},
                location={'line': line_number, 'column': 0},
                children=[]
            )
        return None
    
    def _parse_node_declaration(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse node declaration"""
        match = re.match(r'node\s+(\w+)', line)
        if match:
            node_name = match.group(1)
            return JaseciASTNode(
                node_type='node',
                name=node_name,
                value=line,
                properties={'declaration_type': 'node'},
                location={'line': line_number, 'column': 0},
                children=[]
            )
        return None
    
    def _parse_edge_declaration(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse edge declaration"""
        match = re.match(r'edge\s+(\w+)', line)
        if match:
            edge_name = match.group(1)
            return JaseciASTNode(
                node_type='edge',
                name=edge_name,
                value=line,
                properties={'declaration_type': 'edge'},
                location={'line': line_number, 'column': 0},
                children=[]
            )
        return None
    
    def _parse_can_action(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse can action declaration"""
        match = re.match(r'can\s+(\w+)', line)
        if match:
            action_name = match.group(1)
            return JaseciASTNode(
                node_type='action',
                name=action_name,
                value=line,
                properties={'action_type': 'can'},
                location={'line': line_number, 'column': 0},
                children=[]
            )
        return None
    
    def _parse_spawn_statement(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse spawn statement"""
        return JaseciASTNode(
            node_type='statement',
            name='spawn',
            value=line,
            properties={'statement_type': 'spawn'},
            location={'line': line_number, 'column': 0},
            children=[]
        )
    
    def _parse_visit_statement(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse visit statement"""
        return JaseciASTNode(
            node_type='statement',
            name='visit',
            value=line,
            properties={'statement_type': 'visit'},
            location={'line': line_number, 'column': 0},
            children=[]
        )
    
    def _parse_take_statement(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse take statement"""
        return JaseciASTNode(
            node_type='statement',
            name='take',
            value=line,
            properties={'statement_type': 'take'},
            location={'line': line_number, 'column': 0},
            children=[]
        )
    
    def _parse_report_statement(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse report statement"""
        return JaseciASTNode(
            node_type='statement',
            name='report',
            value=line,
            properties={'statement_type': 'report'},
            location={'line': line_number, 'column': 0},
            children=[]
        )
    
    def _parse_general_statement(self, line: str, line_number: int) -> JaseciASTNode:
        """Parse general statement"""
        return JaseciASTNode(
            node_type='statement',
            name='general',
            value=line,
            properties={'statement_type': 'general'},
            location={'line': line_number, 'column': 0},
            children=[]
        )
    
    async def _generate_osp_elements(
        self, 
        ast_root: JaseciASTNode, 
        project_id: Optional[str] = None
    ) -> Tuple[List[OSPNode], List[OSPRelationship]]:
        """Generate OSP nodes and relationships from Jaseci AST"""
        nodes = []
        relationships = []
        
        # Create module/program node
        module_node = self._create_osp_node(ast_root, project_id)
        nodes.append(module_node)
        
        # Traverse AST and create nodes and relationships
        await self._traverse_ast(ast_root, module_node.id, nodes, relationships, project_id)
        
        return nodes, relationships
    
    async def _traverse_ast(
        self, 
        jaseci_node: JaseciASTNode, 
        parent_id: str, 
        nodes: List[OSPNode], 
        relationships: List[OSPRelationship],
        project_id: Optional[str] = None
    ):
        """Traverse Jaseci AST and create OSP elements"""
        # Create node for current element
        current_node = self._create_osp_node(jaseci_node, project_id)
        nodes.append(current_node)
        
        # Create relationship to parent
        if parent_id:
            rel_type = self._determine_relationship_type(jaseci_node.parent, jaseci_node)
            relationship = OSPRelationship(
                from_node=parent_id,
                to_node=current_node.id,
                relationship_type=rel_type,
                project_id=project_id,
                properties={'ast_context': jaseci_node.properties}
            )
            relationships.append(relationship)
        
        # Process children
        for child in jaseci_node.children:
            await self._traverse_ast(child, current_node.id, nodes, relationships, project_id)
    
    def _create_osp_node(self, jaseci_node: JaseciASTNode, project_id: Optional[str]) -> OSPNode:
        """Create OSP node from Jaseci AST node"""
        self.node_counter += 1
        node_id = f"{jaseci_node.node_type}:{jaseci_node.name}:{self.node_counter}"
        
        # Map Jaseci node type to OSP node type
        osp_node_type = self._map_jaseci_to_osp_node_type(jaseci_node.node_type)
        
        return OSPNode(
            id=node_id,
            node_type=osp_node_type,
            name=jaseci_node.name,
            properties={
                **jaseci_node.properties,
                'jaseci_value': jaseci_node.value,
                'line_count': len(jaseci_node.children),
                'complexity_hints': self._calculate_node_complexity(jaseci_node)
            },
            jaseci_context={
                'original_node_type': jaseci_node.node_type,
                'ast_properties': jaseci_node.properties,
                'children_count': len(jaseci_node.children)
            },
            project_id=project_id,
            line_number=jaseci_node.location.get('line'),
            column_number=jaseci_node.location.get('column')
        )
    
    def _map_jaseci_to_osp_node_type(self, jaseci_type: str) -> NodeType:
        """Map Jaseci node types to OSP node types"""
        mapping = {
            'walker': NodeType.FUNCTION,
            'node': NodeType.CLASS,
            'edge': NodeType.CONSTANT,
            'action': NodeType.METHOD,
            'statement': NodeType.STATEMENT,
            'expression': NodeType.EXPRESSION,
            'variable': NodeType.VARIABLE,
            'import': NodeType.IMPORT,
            'block': NodeType.STATEMENT,
            'identifier': NodeType.VARIABLE,
            'literal': NodeType.CONSTANT,
            'collection': NodeType.VARIABLE,
            'comprehension': NodeType.EXPRESSION,
            'program': NodeType.MODULE
        }
        
        return mapping.get(jaseci_type, NodeType.STATEMENT)
    
    def _determine_relationship_type(self, parent: Optional[JaseciASTNode], child: JaseciASTNode) -> RelationshipType:
        """Determine relationship type between parent and child"""
        if not parent:
            return RelationshipType.CONTAINS
        
        # Define relationship rules based on node types
        parent_type = parent.node_type
        child_type = child.node_type
        
        if parent_type in ['walker', 'node', 'program'] and child_type in ['action', 'statement']:
            return RelationshipType.DEFINES
        elif parent_type == 'walker' and child_type == 'variable':
            return RelationshipType.DEFINES
        elif parent_type == 'node' and child_type in ['action', 'variable']:
            return RelationshipType.DEFINES
        elif child_type == 'import':
            return RelationshipType.IMPORTS
        elif 'call' in child_type.lower():
            return RelationshipType.CALLS
        elif 'reference' in child_type.lower():
            return RelationshipType.REFERENCES
        else:
            return RelationshipType.CONTAINS
    
    def _calculate_node_complexity(self, jaseci_node: JaseciASTNode) -> Dict[str, float]:
        """Calculate complexity hints for a node"""
        complexity_hints = {
            'cyclomatic_increment': 0.0,
            'cognitive_increment': 0.0,
            'nesting_increment': 0.0
        }
        
        # Increment complexity based on node type
        if jaseci_node.node_type in ['if', 'while', 'for', 'try']:
            complexity_hints['cyclomatic_increment'] = 1.0
            complexity_hints['cognitive_increment'] = 1.0
        elif jaseci_node.node_type in ['elif', 'except']:
            complexity_hints['cyclomatic_increment'] = 1.0
            complexity_hints['cognitive_increment'] = 1.0
        elif jaseci_node.node_type == 'nested_block':
            complexity_hints['nesting_increment'] = 1.0
            complexity_hints['cognitive_increment'] = 0.5
        
        return complexity_hints
    
    def _analyze_complexity(self, ast_root: JaseciASTNode) -> CodeComplexityMetrics:
        """Analyze code complexity from AST"""
        metrics = CodeComplexityMetrics()
        
        # Count elements
        node_count = 0
        function_count = 0
        class_count = 0
        max_nesting = 0
        current_nesting = 0
        
        def traverse_for_metrics(node: JaseciASTNode, depth: int = 0):
            nonlocal node_count, function_count, class_count, max_nesting, current_nesting
            
            node_count += 1
            current_nesting = max(current_nesting, depth)
            max_nesting = max(max_nesting, current_nesting)
            
            # Count specific node types
            if node.node_type in ['walker', 'function']:
                function_count += 1
            elif node.node_type == 'node':
                class_count += 1
            
            # Calculate cyclomatic complexity
            if node.node_type in ['if', 'while', 'for', 'try']:
                metrics.cyclomatic_complexity += 1
            elif node.node_type in ['elif', 'except']:
                metrics.cyclomatic_complexity += 1
            
            # Calculate cognitive complexity
            metrics.cognitive_complexity += depth * 0.5
            
            # Process children
            for child in node.children:
                traverse_for_metrics(child, depth + 1)
        
        traverse_for_metrics(ast_root)
        
        # Update metrics
        metrics.nesting_depth = max_nesting
        metrics.function_count = function_count
        metrics.class_count = class_count
        metrics.line_count = ast_root.properties.get('total_lines', 0)
        
        # Calculate maintainability index (simplified)
        # Higher is better (0-100 scale)
        if metrics.line_count > 0:
            halstead_volume = node_count * 2  # Simplified calculation
            metrics.maintainability_index = max(0, 171 - 5.2 * halstead_volume - 0.23 * metrics.cyclomatic_complexity - 16.2 * metrics.nesting_depth)
        
        return metrics
    
    def _generate_insights(
        self, 
        complexity: CodeComplexityMetrics, 
        nodes: List[OSPNode], 
        relationships: List[OSPRelationship]
    ) -> List[str]:
        """Generate insights from analysis"""
        insights = []
        
        # Complexity insights
        if complexity.cyclomatic_complexity > 10:
            insights.append(f"High cyclomatic complexity detected: {complexity.cyclomatic_complexity:.1f}")
        
        if complexity.nesting_depth > 4:
            insights.append(f"Deep nesting found: {complexity.nesting_depth} levels deep")
        
        if complexity.cognitive_complexity > 15:
            insights.append(f"High cognitive complexity: {complexity.cognitive_complexity:.1f}")
        
        # Structure insights
        function_count = sum(1 for node in nodes if node.node_type == NodeType.FUNCTION)
        if function_count > 20:
            insights.append(f"Large number of functions detected: {function_count}")
        
        # Relationship insights
        call_relationships = [rel for rel in relationships if rel.relationship_type == RelationshipType.CALLS]
        if len(call_relationships) > 50:
            insights.append(f"High function call frequency: {len(call_relationships)} calls")
        
        return insights
    
    def _generate_recommendations(
        self, 
        complexity: CodeComplexityMetrics, 
        nodes: List[OSPNode], 
        relationships: List[OSPRelationship]
    ) -> List[str]:
        """Generate recommendations from analysis"""
        recommendations = []
        
        # Complexity recommendations
        if complexity.cyclomatic_complexity > 10:
            recommendations.append("Consider refactoring complex functions to reduce cyclomatic complexity")
        
        if complexity.nesting_depth > 4:
            recommendations.append("Reduce nesting depth by using early returns or extracting methods")
        
        if complexity.cognitive_complexity > 15:
            recommendations.append("Simplify cognitive complexity by breaking down complex logic")
        
        # Structure recommendations
        if complexity.function_count > 20:
            recommendations.append("Consider organizing functions into classes or modules")
        
        # Quality recommendations
        comment_ratio = 0.0  # Calculate if comments are available
        if comment_ratio < 0.1:
            recommendations.append("Add more comments to improve code documentation")
        
        return recommendations