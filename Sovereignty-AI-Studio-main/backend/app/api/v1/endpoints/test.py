from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_database
from app.core.init_db import create_tables

router = APIRouter()


@router.get("/")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    return {"message": "API is working!", "version": "1.0.0"}


@router.post("/init-db")
async def initialize_database():
    """Initialize database tables."""
    try:
        create_tables()
        return {"message": "Database initialized successfully!"}
    except Exception as e:
        return {"error": f"Failed to initialize database: {str(e)}"}


@router.get("/db-test")
async def test_database(db: Session = Depends(get_database)):
    """Test database connection."""
    try:
        result = db.execute("SELECT 1 as test")
        return {
            "message": "Database connection successful!",
            "result": result.scalar(),
        }
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}
