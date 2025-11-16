#!/usr/bin/env python3
"""
Jaseci Learning Companion - Authentication Service
Enterprise-grade authentication and authorization service

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

from database.connection import get_db

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Enterprise authentication service"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secure-secret-key-minimum-32-characters")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_EXPIRATION_HOURS", 24)) * 60
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            async with get_db() as conn:
                # Get user by email
                user = await conn.fetchrow("""
                    SELECT id, email, username, password_hash, first_name, last_name, role, is_active, created_at
                    FROM users 
                    WHERE email = $1 AND is_active = true
                """, email)
                
                if not user:
                    logger.warning(f"User not found or inactive: {email}")
                    return None
                
                # Verify password
                if not self.verify_password(password, user["password_hash"]):
                    logger.warning(f"Invalid password for user: {email}")
                    return None
                
                # Update last login
                await conn.execute("""
                    UPDATE users 
                    SET last_login = $1, login_count = login_count + 1 
                    WHERE id = $2
                """, datetime.utcnow(), user["id"])
                
                # Log successful login
                logger.info(f"User authenticated successfully: {email}")
                
                return dict(user)
                
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def create_user(self, email: str, username: str, password: str, 
                         first_name: str, last_name: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """Create new user account"""
        try:
            # Check if user already exists
            async with get_db() as conn:
                existing = await conn.fetchrow("""
                    SELECT id FROM users WHERE email = $1 OR username = $2
                """, email, username)
                
                if existing:
                    raise ValueError("User with this email or username already exists")
                
                # Create new user
                password_hash = self.get_password_hash(password)
                
                user_id = await conn.fetchval("""
                    INSERT INTO users (email, username, password_hash, first_name, last_name, role, is_active, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, true, $7)
                    RETURNING id
                """, email, username, password_hash, first_name, last_name, role, datetime.utcnow())
                
                # Get created user
                user = await conn.fetchrow("""
                    SELECT id, email, username, first_name, last_name, role, is_active, created_at
                    FROM users WHERE id = $1
                """, user_id)
                
                logger.info(f"User created successfully: {email}")
                return dict(user)
                
        except Exception as e:
            logger.error(f"User creation error for {email}: {e}")
            raise
    
    async def verify_user_email(self, user_id: str, verification_token: str) -> bool:
        """Verify user email with token"""
        try:
            async with get_db() as conn:
                # Verify token and update user status
                result = await conn.execute("""
                    UPDATE users 
                    SET email_verified = true, verification_token = NULL
                    WHERE id = $1 AND verification_token = $2 AND email_verified = false
                """, user_id, verification_token)
                
                if "UPDATE 1" in result:
                    logger.info(f"User email verified: {user_id}")
                    return True
                else:
                    logger.warning(f"Email verification failed for user: {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Email verification error for {user_id}: {e}")
            return False
    
    async def reset_password(self, email: str, new_password: str, reset_token: str) -> bool:
        """Reset user password with reset token"""
        try:
            async with get_db() as conn:
                # Verify reset token and update password
                password_hash = self.get_password_hash(new_password)
                
                result = await conn.execute("""
                    UPDATE users 
                    SET password_hash = $1, reset_token = NULL
                    WHERE email = $2 AND reset_token = $3 AND reset_token_expires > $4
                """, password_hash, email, reset_token, datetime.utcnow())
                
                if "UPDATE 1" in result:
                    logger.info(f"Password reset successful for: {email}")
                    return True
                else:
                    logger.warning(f"Password reset failed for: {email}")
                    return False
                    
        except Exception as e:
            logger.error(f"Password reset error for {email}: {e}")
            return False
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            async with get_db() as conn:
                # Get current user password
                user = await conn.fetchrow("""
                    SELECT password_hash FROM users WHERE id = $1
                """, user_id)
                
                if not user or not self.verify_password(current_password, user["password_hash"]):
                    logger.warning(f"Invalid current password for user: {user_id}")
                    return False
                
                # Update password
                password_hash = self.get_password_hash(new_password)
                
                await conn.execute("""
                    UPDATE users 
                    SET password_hash = $1, last_password_change = $2
                    WHERE id = $3
                """, password_hash, datetime.utcnow(), user_id)
                
                logger.info(f"Password changed successfully for user: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Password change error for {user_id}: {e}")
            return False
    
    async def deactivate_user(self, user_id: str, reason: str = "User request") -> bool:
        """Deactivate user account"""
        try:
            async with get_db() as conn:
                result = await conn.execute("""
                    UPDATE users 
                    SET is_active = false, deactivated_at = $1, deactivation_reason = $2
                    WHERE id = $3
                """, datetime.utcnow(), reason, user_id)
                
                if "UPDATE 1" in result:
                    logger.info(f"User deactivated: {user_id} - Reason: {reason}")
                    return True
                else:
                    logger.warning(f"User deactivation failed: {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"User deactivation error for {user_id}: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> list:
        """Get user permissions"""
        try:
            async with get_db() as conn:
                permissions = await conn.fetch("""
                    SELECT permission_name, resource, action
                    FROM user_permissions up
                    JOIN users u ON up.user_id = u.id
                    WHERE u.id = $1 AND u.is_active = true
                """, user_id)
                
                return [dict(perm) for perm in permissions]
                
        except Exception as e:
            logger.error(f"Permission retrieval error for {user_id}: {e}")
            return []
    
    async def close(self):
        """Close database connections"""
        logger.info("Auth service closed")

# Password reset token generation
def generate_reset_token(email: str) -> str:
    """Generate password reset token"""
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"email": email, "exp": expire}
    return jwt.encode(to_encode, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")

# Email verification token generation
def generate_verification_token(user_id: str) -> str:
    """Generate email verification token"""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(to_encode, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
