#!/usr/bin/env python3
"""
Database initialization script for Sovereignty AI Studio
Creates all tables including the alerts system
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import Base, engine
from app.models import user, alert, project, generation, media

def init_db():
    """Initialize the database with all models"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")
        print("\nTables created:")
        for table in Base.metadata.tables.keys():
            print(f"  - {table}")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
