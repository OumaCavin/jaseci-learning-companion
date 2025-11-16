"""
API Gateway with Authentication
Enterprise FastAPI Gateway for Jaseci Learning Companion

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from uuid import UUID, uuid4

import jwt
from fastapi import (
    FastAPI, HTTPException, Depends, Request, Response, 
    status, BackgroundTasks, WebSocket, WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
import redis.asyncio as redis
import uvicorn
from jose import JWTError
from passlib.context import CryptContext
import bcrypt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Rate Limiting
limiter = Limiter(key_func=get_remote_address)


# Security Configuration
SECRET_KEY = "your-secret-key-here"  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Pydantic Models
class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="student", regex="^(student|instructor|admin)$")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """User profile model"""
    user_id: UUID
    email: EmailStr
    username: str
    full_name: str
    role: str
    is_active: bool
    preferences: Dict[str, Any]
    created_at: datetime
    last_login: Optional[datetime]


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class TokenData(BaseModel):
    """Token data model"""
    user_id: UUID
    role: str
    permissions: Set[str]


class AuthRequest(BaseModel):
    """Authentication request model"""
    action: str  # register, login, refresh, logout
    data: Dict[str, Any]


class UserPreferences(BaseModel):
    """User learning preferences"""
    learning_style: str = Field(default="visual", regex="^(visual|auditory|kinesthetic|reading)$")
    difficulty_level: str = Field(default="intermediate", regex="^(beginner|intermediate|advanced|expert)$")
    language: str = Field(default="en")
    notifications: bool = True
    auto_save: bool = True
    code_theme: str = Field(default="vs-dark")


class LearningProgress(BaseModel):
    """Learning progress tracking"""
    user_id: UUID
    lesson_id: str
    status: str  # not_started, in_progress, completed
    progress_percentage: float = Field(ge=0, le=100)
    time_spent_minutes: int = Field(ge=0)
    last_accessed: datetime
    completed_at: Optional[datetime]


class CodeSubmission(BaseModel):
    """Code submission model"""
    user_id: UUID
    code: str
    language: str = Field(default="jac")
    lesson_id: Optional[str] = None
    exercise_id: Optional[str] = None


class QualityAssessment(BaseModel):
    """Quality assessment results"""
    submission_id: UUID
    overall_score: float = Field(ge=0, le=100)
    correctness_score: float = Field(ge=0, le=100)
    performance_score: float = Field(ge=0, le=100)
    security_score: float = Field(ge=0, le=100)
    code_quality_score: float = Field(ge=0, le=100)
    documentation_score: float = Field(ge=0, le=100)
    feedback: Dict[str, Any]
    recommendations: List[str]


# Authentication Service
class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.active_sessions: Dict[str, Dict] = {}
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
        
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
        
    def create_refresh_token(self, data: dict) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            role: str = payload.get("role", "student")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            token_data = TokenData(
                user_id=UUID(user_id),
                role=role,
                permissions=self._get_role_permissions(role)
            )
            
            return token_data
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
    def _get_role_permissions(self, role: str) -> Set[str]:
        """Get permissions for a role"""
        role_permissions = {
            "student": {"read_progress", "submit_code", "view_assessments"},
            "instructor": {"read_progress", "submit_code", "view_assessments", "create_content", "grade_submissions"},
            "admin": {"read_progress", "submit_code", "view_assessments", "create_content", "grade_submissions", "manage_users", "system_admin"}
        }
        
        return role_permissions.get(role, set())
        
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        try:
            # Get user from Redis
            user_data = await self.redis.hget("users", email)
            
            if not user_data:
                return None
                
            user = eval(user_data)  # In production, use proper JSON serialization
            
            if not self.verify_password(password, user["hashed_password"]):
                return None
                
            # Update last login
            user["last_login"] = datetime.utcnow().isoformat()
            await self.redis.hset("users", email, str(user))
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
            
    async def create_user(self, user_data: UserCreate) -> Dict:
        """Create new user"""
        user_id = str(uuid4())
        hashed_password = self.get_password_hash(user_data.password)
        
        user = {
            "user_id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "preferences": UserPreferences().dict()
        }
        
        # Store user in Redis
        await self.redis.hset("users", user_data.email, str(user))
        await self.redis.hset("usernames", user_data.username, user_id)
        
        logger.info(f"User created: {user_data.email}")
        return user
        
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        user_data = await self.redis.hget("users", email)
        return eval(user_data) if user_data else None
        
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        # Search through all users (in production, use proper indexing)
        users = await self.redis.hgetall("users")
        
        for email, user_data in users.items():
            user = eval(user_data)
            if user["user_id"] == user_id:
                return user
                
        return None
        
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """Update user preferences"""
        # Find user by ID
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
            
        user["preferences"] = preferences.dict()
        await self.redis.hset("users", user["email"], str(user))
        
        return True


# Dependency Functions
async def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    redis_client = redis.from_url("redis://localhost:6379")
    return AuthService(redis_client)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict:
    """Get current authenticated user"""
    token_data = auth_service.verify_token(credentials.credentials)
    user = await auth_service.get_user_by_id(str(token_data.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    return user


async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get current active user"""
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_checker(current_user: Dict = Depends(get_current_active_user)):
        user_permissions = AuthService(None)._get_role_permissions(current_user["role"])
        
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
            
        return current_user
        
    return permission_checker


# Application Factory
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    redis_client = redis.from_url("redis://localhost:6379")
    await redis_client.ping()
    
    # Store in app state
    app.state.redis = redis_client
    
    yield
    
    # Shutdown
    await redis_client.close()


# Create FastAPI application
app = FastAPI(
    title="Jaseci Learning Companion API",
    description="Enterprise Multi-Agent Learning Platform API",
    version="2.0.0-enterprise",
    lifespan=lifespan
)


# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# WebSocket Manager
class WebSocketManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        connection_id = str(uuid4())
        
        self.active_connections[connection_id] = websocket
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id
        
    def disconnect(self, connection_id: str, user_id: str):
        """Disconnect WebSocket"""
        self.active_connections.pop(connection_id, None)
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                self.user_connections.pop(user_id, None)
                
        logger.info(f"WebSocket disconnected: {connection_id}")
        
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send message to {connection_id}: {str(e)}")
                        self.disconnect(connection_id, user_id)
                        
    async def broadcast_message(self, message: dict, user_ids: List[str] = None):
        """Broadcast message to multiple users or all"""
        if user_ids:
            for user_id in user_ids:
                await self.send_personal_message(message, user_id)
        else:
            # Broadcast to all connected users
            for user_id in list(self.user_connections.keys()):
                await self.send_personal_message(message, user_id)


ws_manager = WebSocketManager()


# Authentication Endpoints
@app.post("/api/auth/register", response_model=Token)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register new user"""
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create user
    user = await auth_service.create_user(user_data)
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["user_id"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user["user_id"]}
    )
    
    # Create user profile
    user_profile = UserProfile(
        user_id=UUID(user["user_id"]),
        email=user["email"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        preferences=user["preferences"],
        created_at=datetime.fromisoformat(user["created_at"]),
        last_login=datetime.fromisoformat(user["last_login"]) if user["last_login"] else None
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile
    )


@app.post("/api/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """User login"""
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["user_id"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user["user_id"]}
    )
    
    # Create user profile
    user_profile = UserProfile(
        user_id=UUID(user["user_id"]),
        email=user["email"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        preferences=user["preferences"],
        created_at=datetime.fromisoformat(user["created_at"]),
        last_login=datetime.fromisoformat(user["last_login"]) if user["last_login"] else None
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile
    )


@app.post("/api/auth/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh" or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        user = await auth_service.get_user_by_id(user_id)
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
            
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user["user_id"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = auth_service.create_refresh_token(
            data={"sub": user["user_id"]}
        )
        
        # Create user profile
        user_profile = UserProfile(
            user_id=UUID(user["user_id"]),
            email=user["email"],
            username=user["username"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user["is_active"],
            preferences=user["preferences"],
            created_at=datetime.fromisoformat(user["created_at"]),
            last_login=datetime.fromisoformat(user["last_login"]) if user["last_login"] else None
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_profile
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@app.post("/api/auth/logout")
async def logout(current_user: Dict = Depends(get_current_active_user)):
    """User logout"""
    # In a production system, you would invalidate the refresh token here
    # For now, we'll just return a success message
    
    return {"message": "Successfully logged out"}


# User Profile Endpoints
@app.get("/api/users/me", response_model=UserProfile)
async def get_current_user_profile(current_user: Dict = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserProfile(
        user_id=UUID(current_user["user_id"]),
        email=current_user["email"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        preferences=current_user["preferences"],
        created_at=datetime.fromisoformat(current_user["created_at"]),
        last_login=datetime.fromisoformat(current_user["last_login"]) if current_user["last_login"] else None
    )


@app.put("/api/users/me/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: Dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user preferences"""
    success = await auth_service.update_user_preferences(current_user["user_id"], preferences)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return {"message": "Preferences updated successfully"}


# Code Submission Endpoints
@app.post("/api/code/submit")
@limiter.limit("30/minute")
async def submit_code(
    request: Request,
    submission: CodeSubmission,
    current_user: Dict = Depends(get_current_active_user),
    background_tasks: BackgroundTasks
):
    """Submit code for analysis"""
    submission_id = str(uuid4())
    
    # Store submission temporarily (in production, use proper database)
    submission_data = {
        "submission_id": submission_id,
        "user_id": current_user["user_id"],
        "code": submission.code,
        "language": submission.language,
        "lesson_id": submission.lesson_id,
        "exercise_id": submission.exercise_id,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    
    # Add background task for processing
    background_tasks.add_task(
        process_code_submission,
        submission_data,
        current_user
    )
    
    return {
        "submission_id": submission_id,
        "status": "submitted",
        "message": "Code submitted successfully. Processing will begin shortly."
    }


async def process_code_submission(submission_data: Dict, user: Dict):
    """Background task to process code submission"""
    try:
        # This will be connected to the agent system later
        logger.info(f"Processing code submission {submission_data['submission_id']}")
        
        # Emit progress update via WebSocket
        await ws_manager.send_personal_message(
            {
                "type": "code_submission_status",
                "submission_id": submission_data["submission_id"],
                "status": "processing",
                "message": "Your code is being analyzed..."
            },
            user["user_id"]
        )
        
        # Simulate processing time
        await asyncio.sleep(3)
        
        # Emit completion
        await ws_manager.send_personal_message(
            {
                "type": "code_submission_status",
                "submission_id": submission_data["submission_id"],
                "status": "completed",
                "message": "Code analysis completed."
            },
            user["user_id"]
        )
        
    except Exception as e:
        logger.error(f"Error processing code submission: {str(e)}")
        
        await ws_manager.send_personal_message(
            {
                "type": "code_submission_status",
                "submission_id": submission_data["submission_id"],
                "status": "error",
                "message": "An error occurred while processing your code."
            },
            user["user_id"]
        )


# WebSocket Endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    connection_id = await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_json()
            
            # Echo message back (in production, handle different message types)
            await ws_manager.send_personal_message(
                {
                    "type": "echo",
                    "message": data.get("message", "Hello from WebSocket"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                user_id
            )
            
    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id, user_id)


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway"
    }


# System Status Endpoint
@app.get("/api/system/status")
async def system_status(current_user: Dict = Depends(get_current_active_user)):
    """Get system status"""
    # In production, this would query the actual system status
    return {
        "api_gateway": "healthy",
        "redis": "healthy",
        "message_bus": "healthy",
        "database": "healthy",
        "agents": {
            "learning_progress": "active",
            "quiz_generator": "active",
            "code_analyzer": "active",
            "quality_assessor": "active",
            "content_recommender": "active",
            "analytics": "active"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )