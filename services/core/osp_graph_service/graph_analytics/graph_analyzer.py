"""
Graph Analyzer for OSP Graph Service

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Advanced graph analysis and analytics for OSP graphs,
providing insights, metrics, and recommendations for
code structure and complexity analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, deque
import math
import json
from datetime import datetime

from services.core.osp_graph_service.models.osp_models import (
    OSPNode, OSPRelationship, OSPGraph, OSPAnalysis,
    GraphTopology, NodeType, RelationshipType
)

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """Advanced graph analyzer for OSP graphs"""
    
    def __init__(self):
        """Initialize the graph analyzer"""
        self.analysis_cache = {}
        self.metric_cache = {}
    
    async def analyze_complexity(self, project_id: str) -> OSPAnalysis:
        """Perform comprehensive complexity analysis"""
        try:
            logger.info(f"🔍 Starting complexity analysis for project {project_id}")
            
            # Get graph data from database
            graph_data = await self._get_graph_data(project_id)
            
            if not graph_data:
                return OSPAnalysis(
                    analysis_type="complexity_analysis",
                    project_id=project_id,
                    results={"error": "No graph data found"},
                    metrics={"nodes_analyzed": 0},
                    insights=["No code data available for analysis"],
                    recommendations=["Upload Jaseci code to begin analysis"]
                )
            
            # Perform various analyses
            topology = await self._analyze_topology(graph_data)
            complexity = await self._analyze_code_complexity(graph_data)
            dependencies = await self._analyze_dependencies(graph_data)
            patterns = await self._detect_patterns(graph_data)
            
            # Generate insights and recommendations
            insights = self._generate_complexity_insights(topology, complexity, dependencies, patterns)
            recommendations = self._generate_complexity_recommendations(topology, complexity, dependencies, patterns)
            
            # Create analysis result
            analysis = OSPAnalysis(
                analysis_type="complexity_analysis",
                project_id=project_id,
                results={
                    "topology": topology.dict(),
                    "complexity": complexity,
                    "dependencies": dependencies,
                    "patterns": patterns,
                    "summary": {
                        "total_nodes": topology.node_count,
                        "total_edges": topology.edge_count,
                        "graph_density": topology.density,
                        "complexity_score": self._calculate_overall_complexity(topology, complexity),
                        "maintainability_score": self._calculate_maintainability_score(topology, complexity)
                    }
                },
                metrics={
                    "nodes_analyzed": topology.node_count,
                    "edges_analyzed": topology.edge_count,
                    "analysis_components": 4
                },
                insights=insights,
                recommendations=recommendations
            )
            
            logger.info(f"✅ Complexity analysis completed for project {project_id}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in complexity analysis: {str(e)}")
            raise
    
    async def _get_graph_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get graph data from database"""
        # This would normally query the Neo4j database
        # For now, return sample data structure
        return {
            "nodes": [],
            "relationships": [],
            "project_id": project_id
        }
    
    async def _analyze_topology(self, graph_data: Dict[str, Any]) -> GraphTopology:
        """Analyze graph topology"""
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        node_count = len(nodes)
        edge_count = len(relationships)
        
        # Calculate graph density
        max_possible_edges = node_count * (node_count - 1) if node_count > 1 else 0
        density = edge_count / max_possible_edges if max_possible_edges > 0 else 0
        
        # Calculate average degree
        degree_counts = self._calculate_degree_distribution(nodes, relationships)
        average_degree = sum(degree_counts.values()) / len(degree_counts) if degree_counts else 0
        
        # Find connected components
        connected_components = self._find_connected_components(nodes, relationships)
        
        # Calculate clustering coefficient
        clustering_coefficient = self._calculate_clustering_coefficient(nodes, relationships)
        
        # Find graph diameter (approximation)
        diameter = self._approximate_diameter(nodes, relationships)
        
        # Calculate centrality metrics
        centrality_metrics = self._calculate_centrality_metrics(nodes, relationships)
        
        return GraphTopology(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            average_degree=average_degree,
            diameter=diameter,
            connected_components=len(connected_components),
            clustering_coefficient=clustering_coefficient,
            centrality_metrics=centrality_metrics
        )
    
    def _calculate_degree_distribution(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, int]:
        """Calculate degree distribution for nodes"""
        degree_counts = defaultdict(int)
        
        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                adjacency[from_node].add(to_node)
                adjacency[to_node].add(from_node)
        
        # Calculate degrees
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                degree_counts[node_id] = len(adjacency[node_id])
        
        return dict(degree_counts)
    
    def _find_connected_components(self, nodes: List[Dict], relationships: List[Dict]) -> List[List[str]]:
        """Find connected components using BFS"""
        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                adjacency[from_node].add(to_node)
                adjacency[to_node].add(from_node)
        
        visited = set()
        components = []
        
        for node in nodes:
            node_id = node.get("id")
            if node_id and node_id not in visited:
                component = []
                queue = deque([node_id])
                visited.add(node_id)
                
                while queue:
                    current = queue.popleft()
                    component.append(current)
                    
                    for neighbor in adjacency[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                components.append(component)
        
        return components
    
    def _calculate_clustering_coefficient(self, nodes: List[Dict], relationships: List[Dict]) -> float:
        """Calculate average clustering coefficient"""
        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                adjacency[from_node].add(to_node)
                adjacency[to_node].add(from_node)
        
        clustering_sum = 0
        valid_nodes = 0
        
        for node in nodes:
            node_id = node.get("id")
            if node_id and node_id in adjacency:
                neighbors = adjacency[node_id]
                if len(neighbors) > 1:
                    # Count edges between neighbors
                    edges_between_neighbors = 0
                    possible_edges = len(neighbors) * (len(neighbors) - 1) / 2
                    
                    for neighbor1 in neighbors:
                        for neighbor2 in neighbors:
                            if neighbor1 != neighbor2 and neighbor2 in adjacency[neighbor1]:
                                edges_between_neighbors += 1
                    
                    # Clustering coefficient for this node
                    node_clustering = edges_between_neighbors / (possible_edges * 2) if possible_edges > 0 else 0
                    clustering_sum += node_clustering
                    valid_nodes += 1
        
        return clustering_sum / valid_nodes if valid_nodes > 0 else 0
    
    def _approximate_diameter(self, nodes: List[Dict], relationships: List[Dict]) -> int:
        """Approximate graph diameter using sampling"""
        if len(nodes) <= 1:
            return 0
        
        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                adjacency[from_node].add(to_node)
                adjacency[to_node].add(from_node)
        
        # Sample a few nodes to estimate diameter
        sample_size = min(10, len(nodes))
        max_distance = 0
        
        for i in range(sample_size):
            node_id = nodes[i].get("id")
            if node_id:
                distances = self._bfs_distance(adjacency, node_id)
                max_distance = max(max_distance, max(distances.values()) if distances else 0)
        
        return max_distance
    
    def _bfs_distance(self, adjacency: Dict[str, Set[str]], start_node: str) -> Dict[str, int]:
        """Calculate BFS distances from start node"""
        distances = {start_node: 0}
        queue = deque([start_node])
        
        while queue:
            current = queue.popleft()
            current_distance = distances[current]
            
            for neighbor in adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)
        
        return distances
    
    def _calculate_centrality_metrics(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, float]:
        """Calculate various centrality metrics"""
        # Build adjacency list
        adjacency = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                adjacency[from_node].add(to_node)
                adjacency[to_node].add(from_node)
        
        centrality_metrics = {}
        
        # Degree centrality
        degree_centrality = {}
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                degree_centrality[node_id] = len(adjacency[node_id])
        
        # Betweenness centrality (approximation)
        betweenness_centrality = self._approximate_betweenness_centrality(adjacency)
        
        # Closeness centrality (approximation)
        closeness_centrality = self._approximate_closeness_centrality(adjacency)
        
        centrality_metrics = {
            "max_degree": max(degree_centrality.values()) if degree_centrality else 0,
            "avg_degree": sum(degree_centrality.values()) / len(degree_centrality) if degree_centrality else 0,
            "central_nodes": [node_id for node_id, degree in degree_centrality.items() 
                            if degree > sum(degree_centrality.values()) / len(degree_centrality) * 2]
        }
        
        return centrality_metrics
    
    def _approximate_betweenness_centrality(self, adjacency: Dict[str, Set[str]]) -> Dict[str, float]:
        """Approximate betweenness centrality using sampling"""
        nodes = list(adjacency.keys())
        if len(nodes) <= 2:
            return {node: 0.0 for node in nodes}
        
        betweenness = {node: 0.0 for node in nodes}
        sample_size = min(20, len(nodes))
        
        # Sample source and target pairs
        for _ in range(sample_size):
            source = nodes[hash(str(_)) % len(nodes)]
            target = nodes[hash(str(_ * 2)) % len(nodes)]
            
            if source != target:
                # Find shortest paths (simplified BFS)
                distances = self._bfs_distance(adjacency, source)
                if target in distances:
                    # This is a simplified approximation
                    betweenness[source] += 1
                    betweenness[target] += 1
        
        # Normalize
        max_betweenness = max(betweenness.values()) if betweenness.values() else 1
        return {node: score / max_betweenness for node, score in betweenness.items()}
    
    def _approximate_closeness_centrality(self, adjacency: Dict[str, Set[str]]) -> Dict[str, float]:
        """Approximate closeness centrality"""
        closeness = {}
        
        for node in adjacency.keys():
            distances = self._bfs_distance(adjacency, node)
            total_distance = sum(distances.values())
            if total_distance > 0:
                closeness[node] = (len(distances) - 1) / total_distance
            else:
                closeness[node] = 0.0
        
        return closeness
    
    async def _analyze_code_complexity(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code-specific complexity metrics"""
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        # Count nodes by type
        node_type_counts = defaultdict(int)
        for node in nodes:
            node_type = node.get("node_type", "unknown")
            node_type_counts[node_type] += 1
        
        # Analyze function complexity
        function_nodes = [node for node in nodes if node.get("node_type") == NodeType.FUNCTION]
        
        # Calculate coupling metrics
        coupling_metrics = self._analyze_coupling(nodes, relationships)
        
        # Analyze inheritance and dependency relationships
        inheritance_relationships = [rel for rel in relationships 
                                  if rel.get("relationship_type") == RelationshipType.INHERITS]
        
        import_relationships = [rel for rel in relationships 
                              if rel.get("relationship_type") == RelationshipType.IMPORTS]
        
        call_relationships = [rel for rel in relationships 
                            if rel.get("relationship_type") == RelationshipType.CALLS]
        
        complexity_metrics = {
            "node_type_distribution": dict(node_type_counts),
            "function_count": len(function_nodes),
            "class_count": node_type_counts.get(NodeType.CLASS, 0),
            "coupling_metrics": coupling_metrics,
            "inheritance_depth": self._calculate_inheritance_depth(inheritance_relationships),
            "circular_dependencies": self._detect_circular_dependencies(relationships),
            "fan_out": self._calculate_fan_out(relationships),
            "fan_in": self._calculate_fan_in(relationships),
            "complexity_distribution": self._calculate_complexity_distribution(nodes),
            "code_smells": self._detect_code_smells(nodes, relationships)
        }
        
        return complexity_metrics
    
    def _analyze_coupling(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Analyze coupling between code elements"""
        coupling_scores = {}
        
        # Group relationships by source node
        outgoing_coupling = defaultdict(set)
        incoming_coupling = defaultdict(set)
        
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            rel_type = rel.get("relationship_type")
            
            if from_node and to_node:
                if rel_type in [RelationshipType.CALLS, RelationshipType.REFERENCES, RelationshipType.USES]:
                    outgoing_coupling[from_node].add(to_node)
                    incoming_coupling[to_node].add(from_node)
        
        # Calculate coupling metrics
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                fan_out = len(outgoing_coupling.get(node_id, set()))
                fan_in = len(incoming_coupling.get(node_id, set()))
                coupling_scores[node_id] = {
                    "fan_out": fan_out,
                    "fan_in": fan_in,
                    "total_coupling": fan_out + fan_in
                }
        
        # Summary metrics
        total_fan_out = sum(score["fan_out"] for score in coupling_scores.values())
        total_fan_in = sum(score["fan_in"] for score in coupling_scores.values())
        
        return {
            "node_coupling": coupling_scores,
            "summary": {
                "avg_fan_out": total_fan_out / len(coupling_scores) if coupling_scores else 0,
                "avg_fan_in": total_fan_in / len(coupling_scores) if coupling_scores else 0,
                "highly_coupled_nodes": [node_id for node_id, score in coupling_scores.items() 
                                       if score["total_coupling"] > 5]
            }
        }
    
    def _calculate_inheritance_depth(self, inheritance_relationships: List[Dict]) -> Dict[str, int]:
        """Calculate inheritance depth for classes"""
        # Build inheritance hierarchy
        parent_child_map = defaultdict(set)
        child_parent_map = {}
        
        for rel in inheritance_relationships:
            parent = rel.get("from_node")
            child = rel.get("to_node")
            if parent and child:
                parent_child_map[parent].add(child)
                child_parent_map[child] = parent
        
        # Calculate depth for each class
        depth_map = {}
        for child in child_parent_map:
            depth = 0
            current = child
            while current in child_parent_map:
                current = child_parent_map[current]
                depth += 1
            depth_map[child] = depth
        
        return depth_map
    
    def _detect_circular_dependencies(self, relationships: List[Dict]) -> List[List[str]]:
        """Detect circular dependencies in the graph"""
        # Build dependency graph
        dependencies = defaultdict(set)
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                dependencies[from_node].add(to_node)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, set()):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for node in dependencies:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _calculate_fan_out(self, relationships: List[Dict]) -> Dict[str, int]:
        """Calculate fan-out for each node"""
        fan_out = defaultdict(int)
        
        for rel in relationships:
            from_node = rel.get("from_node")
            if from_node:
                fan_out[from_node] += 1
        
        return dict(fan_out)
    
    def _calculate_fan_in(self, relationships: List[Dict]) -> Dict[str, int]:
        """Calculate fan-in for each node"""
        fan_in = defaultdict(int)
        
        for rel in relationships:
            to_node = rel.get("to_node")
            if to_node:
                fan_in[to_node] += 1
        
        return dict(fan_in)
    
    def _calculate_complexity_distribution(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Calculate complexity distribution across nodes"""
        complexity_scores = []
        
        for node in nodes:
            # Calculate complexity score based on node properties
            node_type = node.get("node_type", "unknown")
            properties = node.get("properties", {})
            
            base_complexity = 1.0
            
            # Add complexity based on node type
            if node_type == NodeType.FUNCTION:
                base_complexity += 2.0
            elif node_type == NodeType.CLASS:
                base_complexity += 3.0
            elif node_type == NodeType.MODULE:
                base_complexity += 1.5
            
            # Add complexity based on properties
            children_count = properties.get("children_count", 0)
            complexity_hints = properties.get("complexity_hints", {})
            
            if isinstance(complexity_hints, dict):
                base_complexity += complexity_hints.get("cyclomatic_increment", 0)
                base_complexity += complexity_hints.get("cognitive_increment", 0) * 0.5
            
            complexity_scores.append(base_complexity)
        
        if not complexity_scores:
            return {"error": "No complexity data available"}
        
        return {
            "min": min(complexity_scores),
            "max": max(complexity_scores),
            "average": sum(complexity_scores) / len(complexity_scores),
            "high_complexity_count": len([score for score in complexity_scores if score > 5.0]),
            "complexity_distribution": {
                "low": len([score for score in complexity_scores if score <= 2.0]),
                "medium": len([score for score in complexity_scores if 2.0 < score <= 5.0]),
                "high": len([score for score in complexity_scores if score > 5.0])
            }
        }
    
    def _detect_code_smells(self, nodes: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Detect code smells in the codebase"""
        code_smells = []
        
        # God Object detection
        large_nodes = [node for node in nodes if len(node.get("properties", {})) > 10]
        if large_nodes:
            code_smells.append({
                "type": "god_object",
                "description": "Nodes with too many properties (potential God Objects)",
                "affected_nodes": [node.get("id") for node in large_nodes],
                "severity": "medium",
                "count": len(large_nodes)
            })
        
        # Long method detection
        function_nodes = [node for node in nodes if node.get("node_type") == NodeType.FUNCTION]
        long_functions = [node for node in function_nodes 
                         if node.get("properties", {}).get("line_count", 0) > 50]
        if long_functions:
            code_smells.append({
                "type": "long_method",
                "description": "Functions that are too long",
                "affected_nodes": [node.get("id") for node in long_functions],
                "severity": "high",
                "count": len(long_functions)
            })
        
        # Cyclomatic complexity detection
        high_complexity_nodes = [node for node in nodes 
                               if node.get("properties", {}).get("complexity_hints", {}).get("cyclomatic_increment", 0) > 5]
        if high_complexity_nodes:
            code_smells.append({
                "type": "high_cyclomatic_complexity",
                "description": "Nodes with very high cyclomatic complexity",
                "affected_nodes": [node.get("id") for node in high_complexity_nodes],
                "severity": "high",
                "count": len(high_complexity_nodes)
            })
        
        return code_smells
    
    async def _analyze_dependencies(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependencies in the codebase"""
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        # Categorize dependencies
        import_deps = [rel for rel in relationships 
                      if rel.get("relationship_type") == RelationshipType.IMPORTS]
        call_deps = [rel for rel in relationships 
                    if rel.get("relationship_type") == RelationshipType.CALLS]
        inherit_deps = [rel for rel in relationships 
                       if rel.get("relationship_type") == RelationshipType.INHERITS]
        
        # Analyze dependency graph
        dependency_metrics = {
            "total_imports": len(import_deps),
            "total_calls": len(call_deps),
            "total_inheritance": len(inherit_deps),
            "dependency_ratio": len(relationships) / len(nodes) if nodes else 0,
            "most_depended_upon": self._find_most_depended_upon_nodes(nodes, relationships),
            "most_dependent": self._find_most_dependent_nodes(nodes, relationships),
            "dependency_layers": self._analyze_dependency_layers(relationships)
        }
        
        return dependency_metrics
    
    def _find_most_depended_upon_nodes(self, nodes: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Find nodes that are depended upon by many others"""
        dependency_count = defaultdict(int)
        
        for rel in relationships:
            to_node = rel.get("to_node")
            if to_node:
                dependency_count[to_node] += 1
        
        # Sort by dependency count
        sorted_deps = sorted(dependency_count.items(), key=lambda x: x[1], reverse=True)
        
        return [{"node_id": node_id, "dependencies": count} for node_id, count in sorted_deps[:10]]
    
    def _find_most_dependent_nodes(self, nodes: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Find nodes that depend on many others"""
        dependent_count = defaultdict(int)
        
        for rel in relationships:
            from_node = rel.get("from_node")
            if from_node:
                dependent_count[from_node] += 1
        
        # Sort by dependent count
        sorted_deps = sorted(dependent_count.items(), key=lambda x: x[1], reverse=True)
        
        return [{"node_id": node_id, "depends_on": count} for node_id, count in sorted_deps[:10]]
    
    def _analyze_dependency_layers(self, relationships: List[Dict]) -> List[List[str]]:
        """Analyze dependency layers using topological sorting"""
        # Build dependency graph
        dependencies = defaultdict(set)
        dependents = defaultdict(set)
        
        for rel in relationships:
            from_node = rel.get("from_node")
            to_node = rel.get("to_node")
            if from_node and to_node:
                dependencies[to_node].add(from_node)
                dependents[from_node].add(to_node)
        
        # Topological sorting to find layers
        layers = []
        remaining = set(dependencies.keys())
        
        while remaining:
            # Find nodes with no dependencies on remaining nodes
            current_layer = []
            for node in remaining:
                if not any(dep in remaining for dep in dependencies[node]):
                    current_layer.append(node)
            
            if not current_layer:
                # Circular dependency detected
                break
            
            layers.append(current_layer)
            remaining -= set(current_layer)
        
        return layers
    
    async def _analyze_patterns(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze architectural patterns in the codebase"""
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        patterns = {
            "detected_patterns": [],
            "pattern_confidence": {},
            "anti_patterns": []
        }
        
        # Detect common design patterns
        patterns["detected_patterns"] = self._detect_design_patterns(nodes, relationships)
        patterns["anti_patterns"] = self._detect_anti_patterns(nodes, relationships)
        
        # Calculate pattern confidence
        patterns["pattern_confidence"] = self._calculate_pattern_confidence(patterns["detected_patterns"])
        
        return patterns
    
    def _detect_design_patterns(self, nodes: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Detect common design patterns"""
        patterns = []
        
        # Detect Factory Pattern
        factory_indicators = self._detect_factory_pattern(nodes, relationships)
        if factory_indicators["confidence"] > 0.5:
            patterns.append({
                "pattern": "factory",
                "confidence": factory_indicators["confidence"],
                "evidence": factory_indicators["evidence"]
            })
        
        # Detect Observer Pattern
        observer_indicators = self._detect_observer_pattern(nodes, relationships)
        if observer_indicators["confidence"] > 0.5:
            patterns.append({
                "pattern": "observer",
                "confidence": observer_indicators["confidence"],
                "evidence": observer_indicators["evidence"]
            })
        
        # Detect MVC Pattern
        mvc_indicators = self._detect_mvc_pattern(nodes, relationships)
        if mvc_indicators["confidence"] > 0.5:
            patterns.append({
                "pattern": "mvc",
                "confidence": mvc_indicators["confidence"],
                "evidence": mvc_indicators["evidence"]
            })
        
        return patterns
    
    def _detect_factory_pattern(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Detect Factory pattern indicators"""
        factory_methods = [node for node in nodes if "factory" in node.get("name", "").lower()]
        creation_methods = [node for node in nodes if "create" in node.get("name", "").lower()]
        
        evidence = []
        confidence = 0.0
        
        if factory_methods:
            evidence.append(f"Found {len(factory_methods)} factory-related methods")
            confidence += 0.3
        
        if creation_methods:
            evidence.append(f"Found {len(creation_methods)} creation methods")
            confidence += 0.4
        
        # Check for instantiation relationships
        instantiation_rels = [rel for rel in relationships 
                            if "creates" in rel.get("relationship_type", "").lower()]
        if instantiation_rels:
            evidence.append(f"Found {len(instantiation_rels)} creation relationships")
            confidence += 0.3
        
        return {"confidence": confidence, "evidence": evidence}
    
    def _detect_observer_pattern(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Detect Observer pattern indicators"""
        # Look for notification/reporting relationships
        notification_rels = [rel for rel in relationships 
                           if "notify" in rel.get("relationship_type", "").lower() or 
                              "report" in rel.get("relationship_type", "").lower()]
        
        evidence = []
        confidence = 0.0
        
        if notification_rels:
            evidence.append(f"Found {len(notification_rels)} notification relationships")
            confidence += 0.5
        
        return {"confidence": confidence, "evidence": evidence}
    
    def _detect_mvc_pattern(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Detect MVC pattern indicators"""
        # Look for controller, model, view keywords
        controllers = [node for node in nodes if "controller" in node.get("name", "").lower()]
        models = [node for node in nodes if "model" in node.get("name", "").lower()]
        views = [node for node in nodes if "view" in node.get("name", "").lower()]
        
        evidence = []
        confidence = 0.0
        
        if controllers:
            evidence.append(f"Found {len(controllers)} controllers")
            confidence += 0.3
        
        if models:
            evidence.append(f"Found {len(models)} models")
            confidence += 0.3
        
        if views:
            evidence.append(f"Found {len(views)} views")
            confidence += 0.4
        
        return {"confidence": confidence, "evidence": evidence}
    
    def _detect_anti_patterns(self, nodes: List[Dict], relationships: List[Dict]) -> List[Dict[str, Any]]:
        """Detect anti-patterns in the codebase"""
        anti_patterns = []
        
        # God Object anti-pattern
        large_classes = [node for node in nodes 
                        if node.get("node_type") == NodeType.CLASS and 
                        len(node.get("properties", {})) > 10]
        if large_classes:
            anti_patterns.append({
                "anti_pattern": "god_object",
                "description": "Classes with too many responsibilities",
                "affected_nodes": [node.get("id") for node in large_classes],
                "severity": "high"
            })
        
        # Spaghetti Code anti-pattern
        spaghetti_indicators = self._detect_spaghetti_code(nodes, relationships)
        if spaghetti_indicators:
            anti_patterns.append({
                "anti_pattern": "spaghetti_code",
                "description": "Complex, tangled code structure",
                "indicators": spaghetti_indicators,
                "severity": "high"
            })
        
        return anti_patterns
    
    def _detect_spaghetti_code(self, nodes: List[Dict], relationships: List[Dict]) -> List[str]:
        """Detect spaghetti code indicators"""
        indicators = []
        
        # High cyclomatic complexity
        high_complexity_count = len([node for node in nodes 
                                   if node.get("properties", {}).get("complexity_hints", {}).get("cyclomatic_increment", 0) > 5])
        if high_complexity_count > 0:
            indicators.append(f"High cyclomatic complexity in {high_complexity_count} nodes")
        
        # Deep nesting
        deep_nesting_count = len([node for node in nodes 
                                if node.get("properties", {}).get("nesting_increment", 0) > 3])
        if deep_nesting_count > 0:
            indicators.append(f"Deep nesting in {deep_nesting_count} nodes")
        
        # Circular dependencies
        circular_deps = self._detect_circular_dependencies(relationships)
        if circular_deps:
            indicators.append(f"Circular dependencies detected in {len(circular_deps)} places")
        
        return indicators
    
    def _calculate_pattern_confidence(self, patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence scores for detected patterns"""
        return {pattern["pattern"]: pattern["confidence"] for pattern in patterns}
    
    def _calculate_overall_complexity(self, topology: GraphTopology, complexity: Dict[str, Any]) -> float:
        """Calculate overall complexity score"""
        # Weighted combination of different complexity measures
        complexity_score = 0.0
        
        # Graph topology complexity
        complexity_score += topology.density * 10  # Density contributes up to 10 points
        complexity_score += min(topology.node_count / 100, 5)  # Node count up to 5 points
        
        # Code complexity
        code_complexity = complexity.get("complexity_distribution", {})
        if isinstance(code_complexity, dict):
            high_complexity = code_complexity.get("high_complexity_count", 0)
            complexity_score += min(high_complexity / 10, 15)  # High complexity nodes up to 15 points
        
        # Coupling complexity
        coupling_metrics = complexity.get("coupling_metrics", {})
        if isinstance(coupling_metrics, dict):
            summary = coupling_metrics.get("summary", {})
            avg_coupling = summary.get("avg_fan_out", 0)
            complexity_score += min(avg_coupling, 10)  # Coupling up to 10 points
        
        return min(complexity_score, 100)  # Cap at 100
    
    def _calculate_maintainability_score(self, topology: GraphTopology, complexity: Dict[str, Any]) -> float:
        """Calculate maintainability score (inverse of complexity)"""
        overall_complexity = self._calculate_overall_complexity(topology, complexity)
        maintainability = max(0, 100 - overall_complexity)
        return maintainability
    
    def _generate_complexity_insights(
        self, 
        topology: GraphTopology, 
        complexity: Dict[str, Any], 
        dependencies: Dict[str, Any], 
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from complexity analysis"""
        insights = []
        
        # Topology insights
        if topology.density > 0.5:
            insights.append(f"High graph density ({topology.density:.2f}) indicates tightly coupled code")
        
        if topology.node_count > 100:
            insights.append(f"Large codebase with {topology.node_count} nodes - consider modularization")
        
        # Complexity insights
        code_complexity = complexity.get("complexity_distribution", {})
        if isinstance(code_complexity, dict):
            high_complexity_count = code_complexity.get("high_complexity_count", 0)
            if high_complexity_count > 0:
                insights.append(f"Found {high_complexity_count} high-complexity nodes requiring attention")
        
        # Dependency insights
        dep_ratio = dependencies.get("dependency_ratio", 0)
        if dep_ratio > 2.0:
            insights.append(f"High dependency ratio ({dep_ratio:.2f}) suggests tight coupling")
        
        # Pattern insights
        detected_patterns = patterns.get("detected_patterns", [])
        if detected_patterns:
            insights.append(f"Detected {len(detected_patterns)} design patterns in the codebase")
        
        # Anti-pattern insights
        anti_patterns = patterns.get("anti_patterns", [])
        if anti_patterns:
            insights.append(f"Found {len(anti_patterns)} anti-patterns requiring refactoring")
        
        return insights
    
    def _generate_complexity_recommendations(
        self, 
        topology: GraphTopology, 
        complexity: Dict[str, Any], 
        dependencies: Dict[str, Any], 
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations from complexity analysis"""
        recommendations = []
        
        # Topology recommendations
        if topology.density > 0.7:
            recommendations.append("Consider reducing coupling by introducing interfaces or abstractions")
        
        if topology.node_count > 200:
            recommendations.append("Large codebase detected - consider splitting into smaller modules")
        
        # Complexity recommendations
        code_complexity = complexity.get("complexity_distribution", {})
        if isinstance(code_complexity, dict):
            high_complexity_count = code_complexity.get("high_complexity_count", 0)
            if high_complexity_count > 5:
                recommendations.append(f"Refactor {high_complexity_count} high-complexity nodes to improve maintainability")
        
        # Coupling recommendations
        coupling_metrics = complexity.get("coupling_metrics", {})
        if isinstance(coupling_metrics, dict):
            summary = coupling_metrics.get("summary", {})
            highly_coupled = summary.get("highly_coupled_nodes", [])
            if highly_coupled:
                recommendations.append(f"Reduce coupling in {len(highly_coupled)} highly coupled nodes")
        
        # Anti-pattern recommendations
        anti_patterns = patterns.get("anti_patterns", [])
        for anti_pattern in anti_patterns:
            if anti_pattern.get("severity") == "high":
                recommendations.append(f"Address high-severity anti-pattern: {anti_pattern.get('anti_pattern')}")
        
        # General recommendations
        if topology.connected_components > 1:
            recommendations.append("Multiple disconnected components found - consider integration")
        
        if topology.clustering_coefficient < 0.1:
            recommendations.append("Low clustering coefficient suggests missing modular structure")
        
        return recommendations