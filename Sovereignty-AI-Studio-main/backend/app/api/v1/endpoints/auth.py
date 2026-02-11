from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.dependencies import get_database
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.user import UserCreate, User, Token, UserLogin
from app.services.user_service import get_user_by_username, get_user_by_email, create_user
from app.config import settings
from app.models.user import User as UserModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def authenticate_and_create_token(
    username: str,
    password: str,
    db: Session
) -> Token:
    """
    Authenticate user credentials and create access token.
    
    This is a shared helper function to avoid code duplication between
    login endpoints.
    
    Args:
        username: Username or email
        password: Plain text password
        db: Database session
        
    Returns:
        Token object with access_token and token_type
        
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If account is inactive
    """
    # Get user by username
    user = get_user_by_username(db, username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_database),
):
    """
    Register a new user account.

    Args:
        user_data: User registration data including username, email, and password
        db: Database session

    Returns:
        User: The newly created user object

    Raises:
        HTTPException 400: If username or email already exists
    """
    # Check if user with username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if user with email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    try:
        new_user = create_user(db, user_data)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database),
):
    """
    Authenticate user and return access token.

    Args:
        form_data: OAuth2 form with username and password
        db: Database session

    Returns:
        Token: Access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    return authenticate_and_create_token(
        username=form_data.username,
        password=form_data.password,
        db=db
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_credentials: UserLogin,
    db: Session = Depends(get_database),
):
    """
    Alternative login endpoint accepting JSON body.

    Args:
        user_credentials: Username and password in JSON format
        db: Database session

    Returns:
        Token: Access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    return authenticate_and_create_token(
        username=user_credentials.username,
        password=user_credentials.password,
        db=db
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_database),
):
    """
    Refresh an access token.

    Args:
        current_token: Current valid access token
        db: Database session

    Returns:
        Token: New access token and token type

    Note:
        This is a basic implementation. For production, implement refresh tokens
        with token rotation and blacklisting.
    """
    from app.dependencies import get_current_user
    
    # Verify the current token and get user
    user = await get_current_user(current_token, db)
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")
