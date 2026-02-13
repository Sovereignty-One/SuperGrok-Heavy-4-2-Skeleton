from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_database, get_current_active_user
from app.core.init_db import create_tables
from app.models.user import User

router = APIRouter()


@router.get("/")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    return {"message": "API is working!", "version": "1.0.0"}


@router.post("/init-db")
async def initialize_database(
    current_user: User = Depends(get_current_active_user),
):
    """
    Initialize database tables (PROTECTED - requires authentication).
    
    WARNING: This endpoint can destroy existing data. Only use during
    initial setup or with proper backup procedures in place.
    
    Args:
        current_user: Authenticated user (must be active)
        
    Returns:
        Success message if database initialized
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 500: If database initialization fails
        
    Note:
        In production, this should only be accessible to admin users.
        Consider adding role-based access control.
    """
    try:
        create_tables()
        return {"message": "Database initialized successfully!"}
    except Exception as e:
        # Don't expose internal error details in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database"
        )


@router.get("/db-test")
async def test_database(db: Session = Depends(get_database)):
    """
    Test database connection.
    
    Args:
        db: Database session
        
    Returns:
        Success message with test query result
        
    Raises:
        HTTPException 500: If database connection fails
    """
    try:
        result = db.execute(text("SELECT 1 as test"))
        return {
            "message": "Database connection successful!",
            "result": result.scalar(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
