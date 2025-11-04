"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from backend.auth.service import auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return access token
    
    Note: This is a placeholder implementation.
    In production, verify against user database.
    """
    
    # TODO: Verify credentials against database
    # For now, accept any credentials for demo purposes
    
    # Create tokens
    user_id = "demo_user_123"
    access_token = auth_service.create_access_token(
        user_id=user_id,
        username=request.username,
        roles=["user", "admin"],  # Demo: grant admin role
        permissions=["read", "write", "execute"]
    )
    
    refresh_token = auth_service.create_refresh_token(
        user_id=user_id,
        username=request.username
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.expiration_minutes * 60,
        user={
            "id": user_id,
            "username": request.username,
            "roles": ["user", "admin"]
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token
    """
    
    try:
        # Decode refresh token
        payload = auth_service.decode_token(request.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = auth_service.create_access_token(
            user_id=payload["sub"],
            username=payload["username"],
            roles=["user", "admin"],  # TODO: Load from database
            permissions=["read", "write", "execute"]
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=auth_service.expiration_minutes * 60
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return {
        "user_id": current_user["sub"],
        "username": current_user["username"],
        "roles": current_user.get("roles", []),
        "permissions": current_user.get("permissions", [])
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client should discard token)
    """
    # In a production system, you might want to:
    # - Add token to blacklist
    # - Clear refresh token from database
    # - Log the logout event
    
    return {
        "message": "Logged out successfully",
        "user_id": current_user["sub"]
    }
