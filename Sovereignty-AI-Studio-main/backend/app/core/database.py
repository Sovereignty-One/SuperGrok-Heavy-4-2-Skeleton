from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = None
SessionLocal = None

Base = declarative_base()


def get_engine():
    global engine
    if engine is None:
        engine = create_engine(settings.database_url)
    return engine


def get_session_local():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return SessionLocal


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
