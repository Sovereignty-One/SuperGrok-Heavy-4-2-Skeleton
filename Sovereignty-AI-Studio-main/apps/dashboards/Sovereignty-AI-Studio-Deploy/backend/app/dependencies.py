from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import verify_token
from app.services.user_service import get_user_by_username
from app.models.user import User
from typing import Optional

security = HTTPBearer()


def get_database() -> Session:
    """Get a SQLAlchemy database session for dependency injection.

    Creates and yields a new database session for each request using the
    configured database connection pool.

    Returns:
        Session: An active SQLAlchemy database session

    Note:
        - Session is automatically closed after request completion
        - Uses connection pooling for efficiency
        - Handled by FastAPI's dependency injection system
    """
    return next(get_db())


def get_redis_client():
    """Get a Redis client instance for dependency injection.

    Provides access to the configured Redis connection for caching
    and temporary data storage.

    Returns:
        Redis: An initialized Redis client instance

    Note:
        - Uses connection pooling for efficiency
        - Configured based on application settings
        - Shared across requests but thread-safe
    """
    return get_redis()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database),
) -> User:
    """Validate JWT token and get the current authenticated user.

    Extracts and validates the JWT token from the Authorization header,
    then retrieves the corresponding user from the database.

    Args:
        credentials (HTTPAuthorizationCredentials): The Bearer token credentials
            extracted from the Authorization header
        db (Session): SQLAlchemy database session

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 Unauthorized if:
            - Token is missing or invalid
            - Token is expired
            - User not found in database

    Note:
        - Expects Bearer authentication scheme
        - Verifies token signature and expiration
        - Used as a FastAPI dependency for protected endpoints
        - Automatically extracts token from Authorization header

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.username}"}
        ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    username = verify_token(token)

    if username is None:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current authenticated user and verify their active status.

    Extends get_current_user by adding an additional check for the user's
    active status.

    Args:
        current_user (User): The authenticated user from get_current_user

    Returns:
        User: The authenticated and active user object

    Raises:
        HTTPException: 400 Bad Request if the user account is inactive

    Note:
        - Builds on get_current_user dependency
        - Used for endpoints that require active user accounts
        - Checks is_active flag on user model

    Example:
        ```python
        @app.post("/settings")
        async def update_settings(
            user: User = Depends(get_current_active_user)
        ):
            return {"message": "Settings updated"}
        ```
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_database),
) -> Optional[User]:
    """Attempt to get current user without requiring authentication.

    Similar to get_current_user but doesn't raise an exception if no token
    is provided or if the token is invalid. Useful for endpoints that can
    work with both authenticated and anonymous users.

    Args:
        credentials (Optional[HTTPAuthorizationCredentials]): Optional Bearer
            token credentials from Authorization header
        db (Session): SQLAlchemy database session

    Returns:
        Optional[User]: The authenticated user object if valid credentials
            provided, None otherwise

    Note:
        - Does not raise exceptions for missing/invalid tokens
        - Useful for optional authentication
        - Can handle missing Authorization header
        - Returns None for anonymous users

    Example:
        ```python
        @app.get("/content")
        async def get_content(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"content": "premium content"}
            return {"content": "basic content"}
        ```
    """
    if not credentials:
        return None

    token = credentials.credentials
    username = verify_token(token)

    if username is None:
        return None

    user = get_user_by_username(db, username=username)
    return user
