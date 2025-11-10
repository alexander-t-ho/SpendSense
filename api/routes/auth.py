"""Authentication routes."""

import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from ingest.schema import get_session, User
from api.auth import get_password_hash, create_access_token, verify_password, get_current_user
from api.models import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest):
    """Register a new user."""
    session = get_session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(
            (User.email == request.email) | (User.username == request.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            name=request.name,
            email=request.email,
            username=request.email,  # Use email as username
            password_hash=get_password_hash(request.password),
            is_admin=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username or user.email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Login and get access token."""
    session = get_session()
    try:
        # Find user by username (email) or email
        # Use a simple query with timeout handling
        try:
            user = session.query(User).filter(
                (User.username == request.username) | (User.email == request.username)
            ).first()
        except Exception as db_error:
            session.rollback()
            print(f"Database error during login: {db_error}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database temporarily unavailable. Please try again.",
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not user.password_hash or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username or user.email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"Unexpected error during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again.",
        )
    finally:
        session.close()


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should discard token)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        username=current_user.username,
        is_admin=current_user.is_admin
    )

