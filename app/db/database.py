"""
Database configuration and session management using SQLAlchemy.
Supports MySQL with connection pooling and proper session management.
"""

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
from app.core.config import get_settings
import logging
import os

logger = logging.getLogger(__name__)

# Global engine instance - will be initialized on first use
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


# Create database engine with connection pooling
def create_db_engine() -> Engine:
    """
    Create SQLAlchemy engine with MySQL connection pool.
    
    Returns:
        SQLAlchemy Engine instance
    """
    settings = get_settings()
    db_url = settings.database_url
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=settings.debug,
    )
    
    # Enable foreign key constraints for MySQL
    # Note: SQLite tests will override this with PRAGMA
    def set_foreign_key_checks(dbapi_conn, connection_record):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            cursor.close()
        except Exception:
            # Silently fail for non-MySQL databases
            pass
    
    @event.listens_for(Engine, "connect")
    def on_connect(dbapi_conn, connection_record):
        set_foreign_key_checks(dbapi_conn, connection_record)
    
    return engine


def get_engine() -> Engine:
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create the session factory (lazy initialization)."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
    return _SessionLocal


# Create default session factory reference
# NOTE: This is now handled by get_session_factory() for lazy initialization


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session.
    Use this in FastAPI route handlers.
    
    Yields:
        SQLAlchemy Session
    """
    SessionLocal_factory = get_session_factory()
    db = SessionLocal_factory()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a new database session (for non-async contexts).
    Remember to close the session when done.
    
    Returns:
        SQLAlchemy Session
    """
    SessionLocal_factory = get_session_factory()
    return SessionLocal_factory()


def close_db():
    """Close the database connection pool."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def set_engine(new_engine: Engine):
    """Set a custom engine (used in tests)."""
    global _engine, _SessionLocal
    _engine = new_engine
    _SessionLocal = None  # Reset factory so it uses new engine
