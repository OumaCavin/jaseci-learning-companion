#!/usr/bin/env python3
"""
Jaseci Learning Companion - API Gateway
FastAPI Gateway service for enterprise-grade request routing and management

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import uvicorn
from fastapi import (
    FastAPI, HTTPException, Request, Response, Depends, 
    BackgroundTasks, WebSocket, WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
import redis
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest
import asyncio
import aiohttp
from jose import JWTError, jwt

# Import local modules
from database.connection import get_db, get_redis
from database.neo4j_client import Neo4jClient
from services.auth_service import AuthService
from services.user_management import UserManagementService
from services.notification_service import NotificationService
from services.osp_graph_service_client import OSPGraphServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration')

# Configuration
class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secure-secret-key-minimum-32-characters")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_HOURS", 24)) * 60
    
    # Service URLs
    ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")
    OSP_GRAPH_SERVICE_URL = os.getenv("OSP_GRAPH_SERVICE_URL", "http://localhost:8001")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Data Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="Jaseci code to analyze")
    project_id: Optional[str] = None
    analysis_type: str = Field(default="full", description="Type of analysis: basic, full, osp")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

# Service Clients
class ServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class OrchestratorClient(ServiceClient):
    async def submit_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit task to orchestrator"""
        async with ServiceClient(self.base_url) as client:
            async with client.session.post(
                f"{self.base_url}/tasks/submit",
                json={"task_type": task_type, "payload": payload}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise HTTPException(status_code=response.status, detail="Orchestrator service error")

# Global services
auth_service: Optional[AuthService] = None
user_service: Optional[UserManagementService] = None
notification_service: Optional[NotificationService] = None
osp_client: Optional[OSPGraphServiceClient] = None
redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global auth_service, user_service, notification_service, osp_client, redis_client
    
    try:
        # Initialize services
        auth_service = AuthService()
        user_service = UserManagementService()
        notification_service = NotificationService()
        osp_client = OSPGraphServiceClient(Config.OSP_GRAPH_SERVICE_URL)
        redis_client = get_redis()
        
        logger.info("✅ API Gateway services initialized successfully")
        yield
    finally:
        # Shutdown
        if auth_service:
            await auth_service.close()
        if user_service:
            await user_service.close()
        if notification_service:
            await notification_service.close()
        if osp_client:
            await osp_client.close()
        logger.info("✅ API Gateway services shut down")

# Create FastAPI app
app = FastAPI(
    title="Jaseci Learning Companion API Gateway",
    description="Enterprise-grade API gateway for multi-agent learning platform",
    version="2.0.0-enterprise",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.jaseci-learning.com"]
)

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_minute = datetime.now().strftime("%Y-%m-%d-%H:%M")
    key = f"rate_limit:{client_ip}:{current_minute}"
    
    try:
        current_requests = redis_client.get(key) or 0
        if int(current_requests) >= Config.RATE_LIMIT_REQUESTS:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, Config.RATE_LIMIT_WINDOW)
        pipe.execute()
        
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        return await call_next(request)

app.middleware("http")(rate_limit_middleware)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, 
            Config.SECRET_KEY, 
            algorithms=[Config.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = await user_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check for all services"""
    services_status = {}
    
    try:
        # Check database connections
        async with get_db() as conn:
            await conn.fetchval("SELECT 1")
        services_status["database"] = "healthy"
    except Exception as e:
        services_status["database"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis
        redis_client.ping()
        services_status["redis"] = "healthy"
    except Exception as e:
        services_status["redis"] = f"unhealthy: {str(e)}"
    
    try:
        # Check OSP Graph Service
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Config.OSP_GRAPH_SERVICE_URL}/health") as response:
                services_status["osp_graph_service"] = "healthy" if response.status == 200 else "unhealthy"
    except Exception as e:
        services_status["osp_graph_service"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Orchestrator
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Config.ORCHESTRATOR_URL}/health") as response:
                services_status["orchestrator"] = "healthy" if response.status == 200 else "unhealthy"
    except Exception as e:
        services_status["orchestrator"] = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if all("healthy" in status for status in services_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="2.0.0-enterprise",
        services=services_status
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """User authentication"""
    try:
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode(
            {"sub": str(user["id"]), "exp": datetime.utcnow() + access_token_expires},
            Config.SECRET_KEY,
            algorithm=Config.ALGORITHM
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user["id"]),
                "email": user["email"],
                "username": user["username"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user.get("role", "user")
            }
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")

@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """User registration"""
    try:
        user = await user_service.create_user(**user_data.dict())
        if not user:
            raise HTTPException(status_code=400, detail="User creation failed")
        
        # Authenticate the newly created user
        login_data = LoginRequest(email=user_data.email, password=user_data.password)
        return await login(login_data)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration service error")

@app.get("/users/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@app.post("/analysis/code", response_model=Dict[str, Any])
async def analyze_code(
    request: CodeAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks
):
    """Analyze Jaseci code using orchestrator and OSP service"""
    try:
        # Submit to orchestrator for processing
        orchestrator_client = OrchestratorClient(Config.ORCHESTRATOR_URL)
        
        # Determine analysis type and service
        if request.analysis_type == "osp":
            # Use OSP Graph Service directly
            result = await osp_client.analyze_jaseci_code(
                code=request.code,
                project_id=request.project_id or str(current_user["id"])
            )
        else:
            # Use orchestrator for general code analysis
            result = await orchestrator_client.submit_task(
                task_type="code_analysis",
                payload={
                    "code": request.code,
                    "analysis_type": request.analysis_type,
                    "user_id": str(current_user["id"]),
                    "project_id": request.project_id
                }
            )
        
        return {
            "analysis_id": result.get("analysis_id", "unknown"),
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analysis/{analysis_id}")
async def get_analysis_result(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get analysis result by ID"""
    try:
        # Cache check first
        cached_result = redis_client.get(f"analysis:{analysis_id}")
        if cached_result:
            return json.loads(cached_result)
        
        # Get from orchestrator
        orchestrator_client = OrchestratorClient(Config.ORCHESTRATOR_URL)
        result = await orchestrator_client.submit_task(
            task_type="get_analysis_result",
            payload={"analysis_id": analysis_id, "user_id": str(current_user["id"])}
        )
        
        # Cache result
        redis_client.setex(
            f"analysis:{analysis_id}",
            3600,  # 1 hour
            json.dumps(result, default=str)
        )
        
        return result
    except Exception as e:
        logger.error(f"Get analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")

@app.get("/osp/graph/{project_id}")
async def get_osp_graph(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get OSP graph visualization data"""
    try:
        result = await osp_client.get_graph_visualization(project_id)
        return result
    except Exception as e:
        logger.error(f"OSP graph error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get OSP graph: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            message_type = message_data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to updates for a user/project
                user_id = message_data.get("user_id")
                project_id = message_data.get("project_id")
                
                # Store connection info
                redis_client.set(
                    f"ws_connection:{user_id}:{project_id}",
                    websocket.client.host,
                    ex=3600
                )
                
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "message": f"Subscribed to updates for user {user_id}, project {project_id}"
                }))
            
            elif message_type == "analysis_request":
                # Handle real-time analysis requests
                analysis_type = message_data.get("analysis_type")
                code = message_data.get("code")
                
                # Submit for processing
                orchestrator_client = OrchestratorClient(Config.ORCHESTRATOR_URL)
                result = await orchestrator_client.submit_task(
                    task_type="realtime_analysis",
                    payload={
                        "code": code,
                        "analysis_type": analysis_type,
                        "websocket_id": id(websocket)
                    }
                )
                
                await websocket.send_text(json.dumps({
                    "type": "analysis_result",
                    "data": result
                }))
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Admin routes
@app.get("/admin/analytics")
async def get_platform_analytics(current_user: dict = Depends(get_current_user)):
    """Get platform-wide analytics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get various platform metrics
        analytics = {
            "total_users": await user_service.get_total_users(),
            "active_users_today": await user_service.get_active_users_today(),
            "total_analyses": await user_service.get_total_analyses(),
            "osp_graphs_created": await user_service.get_osp_graphs_count(),
            "system_health": "operational"
        }
        return analytics
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
