"""
Authentication API endpoints for login, logout, and token validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.db.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_user_id_from_token
from app.core.config import get_settings
from app.models import User
from app.schemas import LoginRequest, TokenResponse, MeResponse, UserCreate, UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login endpoint.
    Validates credentials and returns JWT access token.
    
    Security:
    - Does not reveal whether email exists or not (generic error message)
    - Uses Argon2 password hashing
    - Rate limiting should be applied at deployment
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Verify user exists and password matches
    if not user or not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {request.email}")
        # Generic error - don't reveal if user exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create JWT token
    access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }


@router.get("/me", response_model=MeResponse)
async def get_current_user(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]
    user_id = get_user_id_from_token(token)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.post("/logout")
async def logout():
    """
    Logout endpoint (stateless JWT).
    In stateless JWT, logout is typically handled client-side by discarding the token.
    This endpoint provides a consistent logout endpoint for clients.
    """
    return {"message": "Logged out successfully. Please discard your token."}


@router.post("/token", response_model=TokenResponse)
async def refresh_token(authorization: str = None):
    """
    Token refresh endpoint placeholder.
    Current implementation uses simple JWT with expiration.
    For production, implement refresh tokens separately.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not yet implemented"
    )
