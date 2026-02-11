from sqlalchemy.orm import Session
from app.core.database import get_engine, Base
from app.models.user import User
from app.models.project import Project
from app.models.generation import Generation
from app.models.media import Media


def init_db():
    """Initialize the database with tables."""
    Base.metadata.create_all(bind=get_engine())


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=get_engine())


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=get_engine())


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
