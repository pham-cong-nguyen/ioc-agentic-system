"""
Authentication and Authorization Service
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidTokenError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_minutes = settings.JWT_EXPIRATION_MINUTES
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        roles: list[str] = None,
        permissions: list[str] = None,
        extra_claims: Dict[str, Any] = None
    ) -> str:
        """Create JWT access token"""
        
        expire = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(
        self,
        user_id: str,
        username: str
    ) -> str:
        """Create JWT refresh token (longer expiration)"""
        
        expire = datetime.utcnow() + timedelta(days=7)
        
        payload = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except (DecodeError, InvalidTokenError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Verify token from Authorization header"""
        token = credentials.credentials
        return self.decode_token(token)
    
    def check_permission(
        self,
        token_payload: Dict[str, Any],
        required_permission: str
    ) -> bool:
        """Check if user has required permission"""
        permissions = token_payload.get("permissions", [])
        roles = token_payload.get("roles", [])
        
        # Admin role has all permissions
        if "admin" in roles:
            return True
        
        # Check specific permission
        if required_permission in permissions:
            return True
        
        return False
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        async def permission_checker(
            token_payload: Dict[str, Any] = Depends(self.verify_token)
        ):
            if not self.check_permission(token_payload, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
            return token_payload
        
        return permission_checker
    
    def require_role(self, role: str):
        """Decorator to require specific role"""
        async def role_checker(
            token_payload: Dict[str, Any] = Depends(self.verify_token)
        ):
            roles = token_payload.get("roles", [])
            if role not in roles and "admin" not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role denied: {role} required"
                )
            return token_payload
        
        return role_checker


# Keycloak integration (optional)
class KeycloakService:
    """Keycloak authentication service"""
    
    def __init__(self):
        self.enabled = bool(settings.KEYCLOAK_URL)
        if self.enabled:
            self.url = settings.KEYCLOAK_URL
            self.realm = settings.KEYCLOAK_REALM
            self.client_id = settings.KEYCLOAK_CLIENT_ID
            self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Keycloak"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Keycloak authentication not configured"
            )
        
        # TODO: Implement Keycloak authentication
        # This would use the python-keycloak library
        # For now, return placeholder
        raise NotImplementedError("Keycloak integration not implemented")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify token with Keycloak"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Keycloak authentication not configured"
            )
        
        # TODO: Implement Keycloak token verification
        raise NotImplementedError("Keycloak integration not implemented")


# Global auth service instances
auth_service = AuthService()
keycloak_service = KeycloakService()


# Convenience dependency for FastAPI routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user from token"""
    return auth_service.verify_token(credentials)


async def require_admin(
    token_payload: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin role"""
    roles = token_payload.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return token_payload
