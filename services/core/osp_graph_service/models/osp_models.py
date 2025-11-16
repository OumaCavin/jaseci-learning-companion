"""
OSP Data Models for Jaseci Learning Companion

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Data models for OSP (Object-Subject-Predicate) graph structures,
representing code relationships and analysis results.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import json


class NodeType(str, Enum):
    """Enumeration of possible node types in OSP graph"""
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    MODULE = "module"
    IMPORT = "import"
    COMMENT = "comment"
    PARAMETER = "parameter"
    CONSTANT = "constant"
    PROPERTY = "property"
    METHOD = "method"
    DECORATOR = "decorator"
    STATEMENT = "statement"
    EXPRESSION = "expression"


class RelationshipType(str, Enum):
    """Enumeration of possible relationship types in OSP graph"""
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    USES = "uses"
    CONTAINS = "contains"
    DEFINES = "defines"
    RETURNS = "returns"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    OVERRIDES = "overrides"
    IMPLEMENTS = "implements"
    CREATES = "creates"
    MODIFIES = "modifies"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"


class JaseciNodeType(str, Enum):
    """Jaseci-specific node types"""
    WALKER = "walker"
    NODE = "node"
    EDGE = "edge"
    ACTION = "action"
    SNIPPET = "snippet"
    CANVAS = "canvas"
    ARCHITYPE = "architype"
    VISITOR = "visitor"
    PROGRAM = "program"
    BLOCK = "block"


class OSPNode(BaseModel):
    """OSP Node model representing a code element"""
    
    id: Optional[str] = Field(None, description="Unique node identifier")
    node_type: Union[NodeType, JaseciNodeType] = Field(..., description="Type of the node")
    name: str = Field(..., description="Name/identifier of the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    jaseci_context: Optional[Dict[str, Any]] = Field(None, description="Jaseci-specific context")
    project_id: Optional[str] = Field(None, description="Project identifier")
    file_path: Optional[str] = Field(None, description="Source file path")
    line_number: Optional[int] = Field(None, description="Line number in source")
    column_number: Optional[int] = Field(None, description="Column number in source")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            "id": self.id,
            "node_type": self.node_type,
            "name": self.name,
            "properties": self.properties,
            "jaseci_context": self.jaseci_context,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class OSPRelationship(BaseModel):
    """OSP Relationship model representing connections between nodes"""
    
    id: Optional[str] = Field(None, description="Unique relationship identifier")
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
    project_id: Optional[str] = Field(None, description="Project identifier")
    weight: float = Field(1.0, description="Relationship weight/strength")
    confidence: float = Field(1.0, description="Relationship confidence score")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary"""
        return {
            "id": self.id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "relationship_type": self.relationship_type,
            "properties": self.properties,
            "project_id": self.project_id,
            "weight": self.weight,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OSPGraph(BaseModel):
    """OSP Graph model containing nodes and relationships"""
    
    id: Optional[str] = Field(None, description="Graph identifier")
    name: Optional[str] = Field(None, description="Graph name")
    project_id: Optional[str] = Field(None, description="Project identifier")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Graph nodes")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Graph relationships")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    def get_node_count(self) -> int:
        """Get number of nodes in graph"""
        return len(self.nodes)
    
    def get_relationship_count(self) -> int:
        """Get number of relationships in graph"""
        return len(self.relationships)
    
    def get_node_types(self) -> List[str]:
        """Get unique node types in graph"""
        return list(set(node.get("node_type") for node in self.nodes))
    
    def get_relationship_types(self) -> List[str]:
        """Get unique relationship types in graph"""
        return list(set(rel.get("relationship_type") for rel in self.relationships))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "nodes": self.nodes,
            "relationships": self.relationships,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "statistics": {
                "node_count": self.get_node_count(),
                "relationship_count": self.get_relationship_count(),
                "node_types": self.get_node_types(),
                "relationship_types": self.get_relationship_types()
            }
        }


class OSPQuery(BaseModel):
    """OSP Query model for graph database queries"""
    
    query_type: str = Field(..., description="Type of query (paths, neighbors, patterns, subgraph)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    limit: Optional[int] = Field(100, description="Result limit")
    project_id: Optional[str] = Field(None, description="Project filter")
    include_metadata: bool = Field(True, description="Include metadata in results")
    
    class Config:
        schema_extra = {
            "example": {
                "query_type": "neighbors",
                "parameters": {
                    "node_id": "function:main_func:default",
                    "depth": 2
                },
                "limit": 50,
                "project_id": "jaseci-project-1"
            }
        }


class OSPSubgraph(BaseModel):
    """OSP Subgraph model for extracted graph portions"""
    
    id: Optional[str] = Field(None, description="Subgraph identifier")
    parent_graph_id: Optional[str] = Field(None, description="Parent graph ID")
    center_node_id: Optional[str] = Field(None, description="Center node for subgraph")
    nodes: List[OSPNode] = Field(default_factory=list, description="Subgraph nodes")
    relationships: List[OSPRelationship] = Field(default_factory=list, description="Subgraph relationships")
    extraction_method: Optional[str] = Field(None, description="Method used for extraction")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Subgraph properties")


class OSPAnalysis(BaseModel):
    """OSP Analysis model for graph analysis results"""
    
    id: Optional[str] = Field(None, description="Analysis identifier")
    analysis_type: str = Field(..., description="Type of analysis")
    project_id: str = Field(..., description="Project identifier")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    metrics: Dict[str, Any] = Field(..., description="Analysis metrics")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "complexity_analysis",
                "project_id": "jaseci-project-1",
                "results": {
                    "cyclomatic_complexity": 15.2,
                    "max_nesting_depth": 4,
                    "cognitive_complexity": 23.7
                },
                "metrics": {
                    "nodes_analyzed": 150,
                    "relationships_analyzed": 234,
                    "analysis_duration": 2.34
                },
                "insights": [
                    "High cyclomatic complexity detected in main function",
                    "Deep nesting found in conditional blocks"
                ],
                "recommendations": [
                    "Refactor complex functions into smaller units",
                    "Reduce nesting depth by using early returns"
                ]
            }
        }


class JaseciCodeElement(BaseModel):
    """Jaseci code element model for AST parsing"""
    
    element_type: str = Field(..., description="Type of code element")
    name: Optional[str] = Field(None, description="Element name")
    value: Optional[str] = Field(None, description="Element value")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Element properties")
    children: List['JaseciCodeElement'] = Field(default_factory=list, description="Child elements")
    location: Optional[Dict[str, int]] = Field(None, description="Source location")
    ast_node: Optional[Dict[str, Any]] = Field(None, description="Original AST node")
    
    def add_child(self, child: 'JaseciCodeElement'):
        """Add child element"""
        self.children.append(child)
    
    def to_osp_node(self, project_id: str = None) -> OSPNode:
        """Convert to OSP node"""
        return OSPNode(
            node_type=self.element_type,
            name=self.name or self.value or f"anonymous_{self.element_type}",
            properties=self.properties,
            jaseci_context={
                "ast_node": self.ast_node,
                "value": self.value,
                "children_count": len(self.children)
            },
            project_id=project_id,
            line_number=self.location.get("line") if self.location else None,
            column_number=self.location.get("column") if self.location else None
        )


class CodeComplexityMetrics(BaseModel):
    """Code complexity metrics model"""
    
    cyclomatic_complexity: float = Field(0.0, description="Cyclomatic complexity")
    cognitive_complexity: float = Field(0.0, description="Cognitive complexity")
    nesting_depth: int = Field(0, description="Maximum nesting depth")
    function_count: int = Field(0, description="Number of functions")
    class_count: int = Field(0, description="Number of classes")
    line_count: int = Field(0, description="Total line count")
    comment_ratio: float = Field(0.0, description="Comment to code ratio")
    maintainability_index: float = Field(0.0, description="Maintainability index")


class GraphTopology(BaseModel):
    """Graph topology analysis model"""
    
    node_count: int = Field(..., description="Total number of nodes")
    edge_count: int = Field(..., description="Total number of edges")
    density: float = Field(..., description="Graph density")
    average_degree: float = Field(..., description="Average node degree")
    diameter: Optional[int] = Field(None, description="Graph diameter")
    connected_components: int = Field(..., description="Number of connected components")
    clustering_coefficient: float = Field(..., description="Average clustering coefficient")
    centrality_metrics: Dict[str, float] = Field(default_factory=dict, description="Centrality metrics")


class OSPVisualizationConfig(BaseModel):
    """Configuration for OSP graph visualization"""
    
    layout: str = Field("force-directed", description="Graph layout algorithm")
    node_size_mapping: Dict[str, int] = Field(default_factory=dict, description="Node size by type")
    node_color_mapping: Dict[str, str] = Field(default_factory=dict, description="Node color by type")
    edge_width_mapping: Dict[str, int] = Field(default_factory=dict, description="Edge width by type")
    edge_color_mapping: Dict[str, str] = Field(default_factory=dict, description="Edge color by type")
    animation_settings: Dict[str, Any] = Field(default_factory=dict, description="Animation settings")
    interaction_settings: Dict[str, Any] = Field(default_factory=dict, description="Interaction settings")


# Update forward references
JaseciCodeElement.model_rebuild()


class OSPExportFormat(str, Enum):
    """Supported export formats for OSP graphs"""
    JSON = "json"
    GRAPHML = "graphml"
    GEXF = "gexf"
    DOT = "dot"
    CSV = "csv"
    NEO4J_IMPORT = "neo4j_import"


class OSPGraphExporter(BaseModel):
    """Graph export configuration and utilities"""
    
    format: OSPExportFormat = Field(..., description="Export format")
    include_metadata: bool = Field(True, description="Include metadata in export")
    compress: bool = Field(False, description="Compress output")
    encoding: str = Field("utf-8", description="Text encoding")
    
    class Config:
        use_enum_values = True


class OSPSearchQuery(BaseModel):
    """Search query for OSP graphs"""
    
    query_text: str = Field(..., description="Search text")
    search_type: str = Field("fulltext", description="Type of search (fulltext, regex, semantic)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(50, description="Results limit")
    project_id: Optional[str] = Field(None, description="Project filter")
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "function main",
                "search_type": "fulltext",
                "filters": {
                    "node_type": "function",
                    "project_id": "jaseci-project-1"
                },
                "limit": 20
            }
        }