"""
Neo4j Client for OSP Graph Service

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Neo4j database client providing OSP graph database operations
for the Jaseci Learning Companion system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import Neo4jError, ConstraintError
import json
from datetime import datetime

from services.core.osp_graph_service.models.osp_models import (
    OSPNode, OSPRelationship, OSPGraph, OSPQuery, OSPAnalysis
)

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client for OSP graph operations"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j client"""
        self.uri = uri or "bolt://localhost:7687"
        self.user = user or "neo4j"
        self.password = password or "password"
        self.driver = None
        
    async def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=50,
                connection_timeout=30
            )
            
            # Test connection
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.consume()
                
            logger.info(f"✅ Connected to Neo4j at {self.uri}")
            
            # Initialize database schema
            await self._initialize_schema()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("🔌 Disconnected from Neo4j")
    
    async def _initialize_schema(self):
        """Initialize database schema and constraints"""
        async with self.driver.session() as session:
            # Create constraints for better performance
            constraints = [
                "CREATE CONSTRAINT node_id IF NOT EXISTS FOR (n:OSPNode) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (n:OSPNode) REQUIRE n.project_id IS NOT NULL",
                "CREATE CONSTRAINT node_type IF NOT EXISTS FOR (n:OSPNode) REQUIRE n.node_type IS NOT NULL",
                "CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.relationship_type)",
                "CREATE INDEX project_relationship IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.project_id)",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except ConstraintError:
                    # Constraint already exists, continue
                    pass
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {str(e)}")
            
            logger.info("📋 Neo4j schema initialized")
    
    async def create_nodes(self, nodes: List[OSPNode]) -> OSPGraph:
        """Create OSP nodes in the database"""
        created_nodes = []
        
        async with self.driver.session() as session:
            async with session.begin_transaction() as tx:
                for node in nodes:
                    try:
                        # Generate unique node ID
                        node_id = f"{node.node_type}:{node.name}:{node.project_id or 'default'}"
                        
                        # Create node with properties
                        query = """
                        CREATE (n:OSPNode {
                            id: $node_id,
                            node_type: $node_type,
                            name: $name,
                            properties: $properties,
                            jaseci_context: $jaseci_context,
                            project_id: $project_id,
                            created_at: datetime(),
                            updated_at: datetime()
                        })
                        RETURN n
                        """
                        
                        result = await tx.run(
                            query,
                            node_id=node_id,
                            node_type=node.node_type,
                            name=node.name,
                            properties=node.properties,
                            jaseci_context=node.jaseci_context,
                            project_id=node.project_id
                        )
                        
                        record = await result.single()
                        if record:
                            created_node = record["n"]
                            created_nodes.append({
                                "id": created_node["id"],
                                "node_type": created_node["node_type"],
                                "name": created_node["name"],
                                "properties": created_node["properties"]
                            })
                    
                    except ConstraintError:
                        # Node already exists, update it
                        await self._update_node(tx, node)
                    except Exception as e:
                        logger.error(f"Failed to create node {node.name}: {str(e)}")
                        raise
                
                await tx.commit()
        
        return OSPGraph(nodes=created_nodes, relationships=[])
    
    async def create_relationships(self, relationships: List[OSPRelationship]) -> OSPGraph:
        """Create OSP relationships in the database"""
        created_relationships = []
        
        async with self.driver.session() as session:
            async with session.begin_transaction() as tx:
                for rel in relationships:
                    try:
                        query = """
                        MATCH (from:OSPNode {id: $from_node_id})
                        MATCH (to:OSPNode {id: $to_node_id})
                        CREATE (from)-[r:RELATED_TO {
                            relationship_type: $relationship_type,
                            properties: $properties,
                            project_id: $project_id,
                            created_at: datetime(),
                            weight: $weight
                        }]->(to)
                        RETURN r
                        """
                        
                        result = await tx.run(
                            query,
                            from_node_id=rel.from_node,
                            to_node_id=rel.to_node,
                            relationship_type=rel.relationship_type,
                            properties=rel.properties,
                            project_id=rel.project_id,
                            weight=rel.properties.get("weight", 1.0)
                        )
                        
                        record = await result.single()
                        if record:
                            created_rel = record["r"]
                            created_relationships.append({
                                "from_node": rel.from_node,
                                "to_node": rel.to_node,
                                "relationship_type": rel.relationship_type,
                                "properties": rel.properties,
                                "weight": created_rel["weight"]
                            })
                    
                    except Exception as e:
                        logger.error(f"Failed to create relationship {rel.relationship_type}: {str(e)}")
                        raise
                
                await tx.commit()
        
        return OSPGraph(nodes=[], relationships=created_relationships)
    
    async def _update_node(self, tx, node: OSPNode):
        """Update existing node"""
        node_id = f"{node.node_type}:{node.name}:{node.project_id or 'default'}"
        
        query = """
        MATCH (n:OSPNode {id: $node_id})
        SET n.properties = $properties,
            n.jaseci_context = $jaseci_context,
            n.updated_at = datetime()
        RETURN n
        """
        
        result = await tx.run(
            query,
            node_id=node_id,
            properties=node.properties,
            jaseci_context=node.jaseci_context
        )
        
        return await result.single()
    
    async def execute_query(self, query: OSPQuery) -> OSPGraph:
        """Execute OSP graph query"""
        nodes = []
        relationships = []
        
        async with self.driver.session() as session:
            if query.query_type == "paths":
                result = await self._query_paths(session, query)
            elif query.query_type == "neighbors":
                result = await self._query_neighbors(session, query)
            elif query.query_type == "patterns":
                result = await self._query_patterns(session, query)
            elif query.query_type == "subgraph":
                result = await self._query_subgraph(session, query)
            else:
                raise ValueError(f"Unknown query type: {query.query_type}")
            
            # Process results
            for record in result:
                if "node" in record:
                    node_data = record["node"]
                    nodes.append({
                        "id": node_data["id"],
                        "node_type": node_data["node_type"],
                        "name": node_data["name"],
                        "properties": node_data["properties"]
                    })
                
                if "rel" in record:
                    rel_data = record["rel"]
                    relationships.append({
                        "from_node": record.get("from_id"),
                        "to_node": record.get("to_id"),
                        "relationship_type": rel_data["relationship_type"],
                        "properties": rel_data["properties"]
                    })
        
        return OSPGraph(nodes=nodes, relationships=relationships)
    
    async def _query_paths(self, session: AsyncSession, query: OSPQuery) -> List:
        """Query graph paths"""
        params = query.parameters
        cypher = """
        MATCH path = (start:OSPNode)-[:RELATED_TO*1..$max_depth]-(end:OSPNode)
        WHERE ($project_id IS NULL OR start.project_id = $project_id)
        RETURN path, nodes(path) as path_nodes, relationships(path) as path_rels
        LIMIT $limit
        """
        
        result = await session.run(
            cypher,
            max_depth=params.get("max_depth", 3),
            project_id=query.project_id,
            limit=query.limit
        )
        
        return await result.data()
    
    async def _query_neighbors(self, session: AsyncSession, query: OSPQuery) -> List:
        """Query node neighbors"""
        params = query.parameters
        node_id = params.get("node_id")
        
        cypher = """
        MATCH (n:OSPNode {id: $node_id})-[r:RELATED_TO]-(neighbor:OSPNode)
        WHERE ($project_id IS NULL OR neighbor.project_id = $project_id)
        RETURN neighbor, r, n.id as from_id, neighbor.id as to_id
        LIMIT $limit
        """
        
        result = await session.run(
            cypher,
            node_id=node_id,
            project_id=query.project_id,
            limit=query.limit
        )
        
        return await result.data()
    
    async def _query_patterns(self, session: AsyncSession, query: OSPQuery) -> List:
        """Query graph patterns"""
        params = query.parameters
        pattern = params.get("pattern", "")
        
        cypher = f"""
        MATCH (n1:OSPNode)-[r:RELATED_TO]-(n2:OSPNode)
        WHERE ($project_id IS NULL OR n1.project_id = $project_id)
        AND ($pattern = '' OR n1.node_type CONTAINS $pattern OR n2.node_type CONTAINS $pattern)
        RETURN n1, r, n2, n1.id as from_id, n2.id as to_id
        LIMIT $limit
        """
        
        result = await session.run(
            cypher,
            project_id=query.project_id,
            pattern=pattern,
            limit=query.limit
        )
        
        return await result.data()
    
    async def _query_subgraph(self, session: AsyncSession, query: OSPQuery) -> List:
        """Query subgraph around a node"""
        params = query.parameters
        node_id = params.get("node_id")
        depth = params.get("depth", 2)
        
        cypher = f"""
        MATCH path = (center:OSPNode {{id: $node_id}})-[:RELATED_TO*0..{depth}]-(node:OSPNode)
        WHERE ($project_id IS NULL OR node.project_id = $project_id)
        RETURN DISTINCT node, 
               [rel in relationships(path) | rel] as rels,
               node.id as from_id, center.id as to_id
        LIMIT $limit
        """
        
        result = await session.run(
            cypher,
            node_id=node_id,
            project_id=query.project_id,
            limit=query.limit
        )
        
        return await result.data()
    
    async def get_visualization_data(
        self, 
        project_id: str, 
        layout: str = "force-directed", 
        node_limit: int = 500
    ) -> Dict[str, Any]:
        """Get graph data optimized for visualization"""
        async with self.driver.session() as session:
            # Get nodes
            nodes_query = """
            MATCH (n:OSPNode)
            WHERE ($project_id IS NULL OR n.project_id = $project_id)
            RETURN n.id as id, n.node_type as node_type, n.name as name, n.properties as properties
            ORDER BY n.created_at DESC
            LIMIT $node_limit
            """
            
            nodes_result = await session.run(nodes_query, project_id=project_id, node_limit=node_limit)
            nodes_data = await nodes_result.data()
            
            # Get relationships
            edges_query = """
            MATCH (from:OSPNode)-[r:RELATED_TO]->(to:OSPNode)
            WHERE ($project_id IS NULL OR from.project_id = $project_id)
            RETURN from.id as from, to.id as to, r.relationship_type as relationship_type, r.properties as properties
            LIMIT $edge_limit
            """
            
            edges_result = await session.run(edges_query, project_id=project_id, edge_limit=node_limit * 2)
            edges_data = await edges_result.data()
            
            # Format for visualization
            nodes = []
            for node_data in nodes_data:
                nodes.append({
                    "id": node_data["id"],
                    "label": node_data["name"],
                    "type": node_data["node_type"],
                    "properties": node_data["properties"],
                    "size": self._calculate_node_size(node_data["node_type"]),
                    "color": self._get_node_color(node_data["node_type"])
                })
            
            edges = []
            for edge_data in edges_data:
                edges.append({
                    "from": edge_data["from"],
                    "to": edge_data["to"],
                    "label": edge_data["relationship_type"],
                    "properties": edge_data["properties"],
                    "width": self._calculate_edge_width(edge_data["relationship_type"]),
                    "color": self._get_edge_color(edge_data["relationship_type"])
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "layout": layout,
                "statistics": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "node_types": list(set(node["type"] for node in nodes)),
                    "relationship_types": list(set(edge["label"] for edge in edges))
                }
            }
    
    def _calculate_node_size(self, node_type: str) -> int:
        """Calculate node size based on type"""
        size_mapping = {
            "function": 15,
            "class": 20,
            "variable": 10,
            "module": 25,
            "import": 8,
            "comment": 6,
            "default": 12
        }
        return size_mapping.get(node_type.lower(), 12)
    
    def _get_node_color(self, node_type: str) -> str:
        """Get node color based on type"""
        color_mapping = {
            "function": "#4CAF50",  # Green
            "class": "#2196F3",     # Blue
            "variable": "#FF9800",  # Orange
            "module": "#9C27B0",    # Purple
            "import": "#607D8B",    # Blue Grey
            "comment": "#795548",   # Brown
            "default": "#757575"    # Grey
        }
        return color_mapping.get(node_type.lower(), "#757575")
    
    def _calculate_edge_width(self, relationship_type: str) -> int:
        """Calculate edge width based on relationship type"""
        width_mapping = {
            "calls": 3,
            "imports": 2,
            "inherits": 4,
            "uses": 2,
            "contains": 1,
            "default": 1
        }
        return width_mapping.get(relationship_type.lower(), 1)
    
    def _get_edge_color(self, relationship_type: str) -> str:
        """Get edge color based on relationship type"""
        color_mapping = {
            "calls": "#2196F3",     # Blue
            "imports": "#4CAF50",   # Green
            "inherits": "#9C27B0",  # Purple
            "uses": "#FF9800",      # Orange
            "contains": "#607D8B",  # Blue Grey
            "default": "#757575"    # Grey
        }
        return color_mapping.get(relationship_type.lower(), "#757575")
    
    async def get_graph_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive graph metrics"""
        async with self.driver.session() as session:
            # Node count by type
            node_metrics_query = """
            MATCH (n:OSPNode)
            WHERE ($project_id IS NULL OR n.project_id = $project_id)
            RETURN n.node_type as node_type, count(n) as count
            ORDER BY count DESC
            """
            
            # Relationship metrics
            relationship_metrics_query = """
            MATCH ()-[r:RELATED_TO]-()
            WHERE ($project_id IS NULL OR r.project_id = $project_id)
            RETURN r.relationship_type as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            # Graph statistics
            stats_query = """
            MATCH (n:OSPNode)
            WHERE ($project_id IS NULL OR n.project_id = $project_id)
            WITH count(n) as total_nodes
            MATCH ()-[r:RELATED_TO]-()
            WHERE ($project_id IS NULL OR r.project_id = $project_id)
            WITH total_nodes, count(r) as total_relationships
            RETURN total_nodes, total_relationships, 
                   toFloat(total_relationships) / toFloat(total_nodes) as density
            """
            
            # Execute queries
            node_result = await session.run(node_metrics_query, project_id=project_id)
            rel_result = await session.run(relationship_metrics_query, project_id=project_id)
            stats_result = await session.run(stats_query, project_id=project_id)
            
            node_metrics = await node_result.data()
            rel_metrics = await rel_result.data()
            stats_data = await stats_result.single()
            
            return {
                "project_id": project_id,
                "total_nodes": stats_data["total_nodes"],
                "total_relationships": stats_data["total_relationships"],
                "graph_density": stats_data["density"],
                "node_distribution": {item["node_type"]: item["count"] for item in node_metrics},
                "relationship_distribution": {item["rel_type"]: item["count"] for item in rel_metrics},
                "most_connected_nodes": await self._get_most_connected_nodes(session, project_id),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    async def _get_most_connected_nodes(self, session: AsyncSession, project_id: str, limit: int = 10) -> List[Dict]:
        """Get most connected nodes"""
        query = """
        MATCH (n:OSPNode)-[r:RELATED_TO]-()
        WHERE ($project_id IS NULL OR n.project_id = $project_id)
        WITH n, count(r) as connections
        ORDER BY connections DESC
        RETURN n.id as id, n.name as name, n.node_type as node_type, connections
        LIMIT $limit
        """
        
        result = await session.run(query, project_id=project_id, limit=limit)
        return await result.data()
    
    async def store_analysis_result(self, analysis: OSPAnalysis, project_id: str):
        """Store analysis result in database"""
        async with self.driver.session() as session:
            query = """
            CREATE (a:OSPAnalysis {
                project_id: $project_id,
                analysis_type: $analysis_type,
                results: $results,
                metrics: $metrics,
                created_at: datetime()
            })
            """
            
            await session.run(
                query,
                project_id=project_id,
                analysis_type=analysis.analysis_type,
                results=analysis.results,
                metrics=analysis.metrics
            )
    
    async def delete_project_graph(self, project_id: str) -> Dict[str, int]:
        """Delete all graph data for a project"""
        async with self.driver.session() as session:
            async with session.begin_transaction() as tx:
                # Count nodes and relationships before deletion
                count_query = """
                MATCH (n:OSPNode {project_id: $project_id})
                WITH count(n) as nodes_count
                MATCH ()-[r:RELATED_TO {project_id: $project_id}]-()
                WITH nodes_count, count(r) as rel_count
                RETURN nodes_count, rel_count
                """
                
                count_result = await tx.run(count_query, project_id=project_id)
                count_data = await count_result.single()
                
                # Delete relationships first (foreign key constraint)
                rel_delete_query = """
                MATCH ()-[r:RELATED_TO {project_id: $project_id}]-()
                DELETE r
                """
                
                await tx.run(rel_delete_query, project_id=project_id)
                
                # Delete nodes
                node_delete_query = """
                MATCH (n:OSPNode {project_id: $project_id})
                DELETE n
                """
                
                await tx.run(node_delete_query, project_id=project_id)
                
                await tx.commit()
                
                return {
                    "nodes_deleted": count_data["nodes_count"],
                    "relationships_deleted": count_data["rel_count"]
                }