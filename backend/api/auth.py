"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import timedelta

from backend.utils.auth import verify_password, create_access_token
from backend.core.config import get_settings

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    token: str
    expires_in: int

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Admin login endpoint
    
    Returns JWT token for admin authentication
    """
    settings = get_settings()
    
    # Verify admin password
    if not verify_password(request.password, settings.admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Create access token
    access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600  # Convert to seconds
    )