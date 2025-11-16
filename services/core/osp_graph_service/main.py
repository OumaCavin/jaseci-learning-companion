"""
OSP Graph Service - Core Implementation

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Main entry point for the OSP (Object-Subject-Predicate) Graph Service.
Provides comprehensive graph database operations, Jaseci code parsing,
and graph visualization capabilities for the Jaseci Learning Companion.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn

# Local imports
from services.core.osp_graph_service.database.neo4j_client import Neo4jClient
from services.core.osp_graph_service.models.osp_models import (
    OSPNode, OSPRelationship, OSPGraph, OSPQuery, OSPAnalysis
)
from services.core.osp_graph_service.jaseci_parser.jaseci_ast_parser import JaseciASTParser
from services.core.osp_graph_service.graph_analytics.graph_analyzer import GraphAnalyzer
from services.core.osp_graph_service.utils.logging_config import setup_logging

# Initialize logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting OSP Graph Service")
    
    # Initialize Neo4j connection
    app.state.neo4j_client = Neo4jClient()
    await app.state.neo4j_client.connect()
    
    # Initialize Jaseci parser
    app.state.jaseci_parser = JaseciASTParser()
    
    # Initialize graph analyzer
    app.state.graph_analyzer = GraphAnalyzer()
    
    logger.info("✅ OSP Graph Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OSP Graph Service")
    if hasattr(app.state, 'neo4j_client'):
        await app.state.neo4j_client.disconnect()
    logger.info("✅ OSP Graph Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="OSP Graph Service",
    description="Comprehensive OSP (Object-Subject-Predicate) Graph Database Service for Jaseci Learning Companion",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class OSPNodeCreate(BaseModel):
    """Request model for creating OSP nodes"""
    node_type: str = Field(..., description="Type of node (variable, function, class, etc.)")
    name: str = Field(..., description="Node identifier")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    jaseci_context: Optional[Dict[str, Any]] = Field(None, description="Jaseci AST context")


class OSPRelationshipCreate(BaseModel):
    """Request model for creating OSP relationships"""
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


class JaseciCodeAnalysis(BaseModel):
    """Request model for Jaseci code analysis"""
    code: str = Field(..., description="Jaseci source code to analyze")
    filename: Optional[str] = Field(None, description="Source filename")
    project_id: Optional[str] = Field(None, description="Project identifier")


class OSPGraphQuery(BaseModel):
    """Request model for OSP graph queries"""
    query_type: str = Field(..., description="Type of query (paths, neighbors, patterns, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    limit: Optional[int] = Field(100, description="Result limit")
    project_id: Optional[str] = Field(None, description="Project filter")


# Response models
class OSPGraphResponse(BaseModel):
    """Response model for OSP graph data"""
    success: bool
    graph_data: Optional[OSPGraph] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None


class OSPAnalysisResponse(BaseModel):
    """Response model for graph analysis results"""
    success: bool
    analysis: Optional[OSPAnalysis] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None


# Dependency to get services
async def get_neo4j_client() -> Neo4jClient:
    """Dependency to get Neo4j client"""
    return app.state.neo4j_client


async def get_jaseci_parser() -> JaseciASTParser:
    """Dependency to get Jaseci parser"""
    return app.state.jaseci_parser


async def get_graph_analyzer() -> GraphAnalyzer:
    """Dependency to get graph analyzer"""
    return app.state.graph_analyzer


# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OSP Graph Service",
        "version": "1.0.0",
        "timestamp": "2025-11-16T21:36:21Z"
    }


@app.post("/nodes/create", response_model=OSPGraphResponse)
async def create_osp_nodes(
    nodes: List[OSPNodeCreate],
    project_id: Optional[str] = None,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Create OSP nodes in the graph database"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Convert Pydantic models to internal models
        osp_nodes = []
        for node_data in nodes:
            osp_node = OSPNode(
                node_type=node_data.node_type,
                name=node_data.name,
                properties=node_data.properties,
                jaseci_context=node_data.jaseci_context,
                project_id=project_id
            )
            osp_nodes.append(osp_node)
        
        # Create nodes in Neo4j
        result = await neo4j_client.create_nodes(osp_nodes)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return OSPGraphResponse(
            success=True,
            graph_data=result,
            message=f"Successfully created {len(osp_nodes)} OSP nodes",
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error creating OSP nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create OSP nodes: {str(e)}")


@app.post("/relationships/create", response_model=OSPGraphResponse)
async def create_osp_relationships(
    relationships: List[OSPRelationshipCreate],
    project_id: Optional[str] = None,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Create OSP relationships in the graph database"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Convert Pydantic models to internal models
        osp_relationships = []
        for rel_data in relationships:
            osp_rel = OSPRelationship(
                from_node=rel_data.from_node,
                to_node=rel_data.to_node,
                relationship_type=rel_data.relationship_type,
                properties=rel_data.properties,
                project_id=project_id
            )
            osp_relationships.append(osp_rel)
        
        # Create relationships in Neo4j
        result = await neo4j_client.create_relationships(osp_relationships)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return OSPGraphResponse(
            success=True,
            graph_data=result,
            message=f"Successfully created {len(osp_relationships)} OSP relationships",
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error creating OSP relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create OSP relationships: {str(e)}")


@app.post("/analyze/jaseci", response_model=OSPAnalysisResponse)
async def analyze_jaseci_code(
    request: JaseciCodeAnalysis,
    background_tasks: BackgroundTasks,
    jaseci_parser: JaseciASTParser = Depends(get_jaseci_parser),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Analyze Jaseci code and generate OSP graph"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Parse Jaseci code and generate OSP graph
        analysis_result = await jaseci_parser.parse_and_generate_osp(
            code=request.code,
            filename=request.filename,
            project_id=request.project_id
        )
        
        # Store the analysis result in background (async)
        background_tasks.add_task(
            neo4j_client.store_analysis_result,
            analysis_result,
            request.project_id
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return OSPAnalysisResponse(
            success=True,
            analysis=analysis_result,
            message="Jaseci code successfully analyzed and OSP graph generated",
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error analyzing Jaseci code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze Jaseci code: {str(e)}")


@app.post("/query/graph", response_model=OSPGraphResponse)
async def query_osp_graph(
    query: OSPGraphQuery,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Query OSP graph data"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Convert to internal query model
        osp_query = OSPQuery(
            query_type=query.query_type,
            parameters=query.parameters,
            limit=query.limit,
            project_id=query.project_id
        )
        
        # Execute query
        result = await neo4j_client.execute_query(osp_query)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return OSPGraphResponse(
            success=True,
            graph_data=result,
            message=f"Successfully executed {query.query_type} query",
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error querying OSP graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to query OSP graph: {str(e)}")


@app.get("/graph/visualization/{project_id}")
async def get_graph_visualization(
    project_id: str,
    layout: Optional[str] = "force-directed",
    node_limit: Optional[int] = 500,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Get graph data optimized for visualization"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Get graph visualization data
        visualization_data = await neo4j_client.get_visualization_data(
            project_id=project_id,
            layout=layout,
            node_limit=node_limit
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "success": True,
            "visualization_data": visualization_data,
            "layout": layout,
            "node_count": len(visualization_data.get("nodes", [])),
            "edge_count": len(visualization_data.get("edges", [])),
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"Error getting graph visualization data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {str(e)}")


@app.post("/analyze/complexity", response_model=OSPAnalysisResponse)
async def analyze_graph_complexity(
    project_id: str,
    graph_analyzer: GraphAnalyzer = Depends(get_graph_analyzer)
):
    """Analyze graph complexity and provide insights"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Perform complexity analysis
        analysis = await graph_analyzer.analyze_complexity(project_id)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return OSPAnalysisResponse(
            success=True,
            analysis=analysis,
            message="Graph complexity analysis completed",
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error analyzing graph complexity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze graph complexity: {str(e)}")


@app.get("/analytics/metrics/{project_id}")
async def get_graph_metrics(
    project_id: str,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Get comprehensive graph metrics"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Get graph metrics
        metrics = await neo4j_client.get_graph_metrics(project_id)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "success": True,
            "metrics": metrics,
            "project_id": project_id,
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"Error getting graph metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph metrics: {str(e)}")


@app.delete("/graph/{project_id}")
async def delete_project_graph(
    project_id: str,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    """Delete all graph data for a project"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Delete project graph
        result = await neo4j_client.delete_project_graph(project_id)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "success": True,
            "message": f"Successfully deleted graph data for project {project_id}",
            "deleted_nodes": result.get("nodes_deleted", 0),
            "deleted_relationships": result.get("relationships_deleted", 0),
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"Error deleting project graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project graph: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )