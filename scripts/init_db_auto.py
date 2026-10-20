#!/usr/bin/env python3
"""
Automatic database initialization script for fraud detection system.
Requires environment variables to be set.
"""

import logging
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import engine
from app.db.base import Base
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def create_database_and_user():
    """Create database and application user."""
    settings = get_settings()
    
    # Parse connection details
    db_url = settings.database_url
    # Format: mysql+pymysql://user:password@host:port/database
    
    try:
        # Connect as admin
        admin_url = f"mysql+pymysql://root:Sushanth2005@localhost:3306/"
        admin_engine = create_engine(admin_url, echo=False)
        
        with admin_engine.connect() as conn:
            # Create database if not exists
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            logger.info(f"✓ Database '{settings.db_name}' created/verified")
            
            # Create user if not exists
            conn.execute(text(f"CREATE USER IF NOT EXISTS '{settings.db_user}'@'localhost' IDENTIFIED BY '{settings.db_password}'"))
            logger.info(f"✓ User '{settings.db_user}' created/verified")
            
            # Grant privileges
            conn.execute(text(f"GRANT ALL PRIVILEGES ON {settings.db_name}.* TO '{settings.db_user}'@'localhost'"))
            conn.execute(text("FLUSH PRIVILEGES"))
            logger.info(f"✓ Privileges granted to '{settings.db_user}'")
            
            conn.commit()
        
        admin_engine.dispose()
        
    except Exception as e:
        logger.error(f"✗ Failed to create database/user: {e}")
        raise


def create_tables():
    """Create all database tables from ORM models."""
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info(f"✓ All tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            logger.info(f"✓ Tables in database: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        raise


def verify_connection():
    """Verify database connection works."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✓ Database connection verified")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def main():
    """Main initialization flow."""
    logger.info("=" * 60)
    logger.info("Database Initialization (Auto)")
    logger.info("=" * 60)
    
    settings = get_settings()
    logger.info(f"Database: {settings.db_name}")
    logger.info(f"User: {settings.db_user}")
    logger.info(f"Host: {settings.db_host}:{settings.db_port}")
    
    try:
        logger.info("\n[1/4] Creating database and user...")
        create_database_and_user()
        
        logger.info("\n[2/4] Verifying connection...")
        if not verify_connection():
            raise Exception("Connection verification failed")
        
        logger.info("\n[3/4] Creating tables...")
        create_tables()
        
        logger.info("\n[4/4] Initialization complete!")
        logger.info("=" * 60)
        logger.info("✓ Database initialization successful!")
        logger.info("\nNext steps:")
        logger.info("1. Create admin user: python scripts/create_admin.py")
        logger.info("2. Seed fraud rules: python scripts/seed_rules.py")
        logger.info("3. Start API: python run.py")
        logger.info("4. Start Dashboard: streamlit run dashboard/app.py")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("1. Verify MySQL is running: mysql -u root -p")
        logger.error("2. Check .env file has correct credentials")
        logger.error("3. Ensure MySQL root user exists and password is correct")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
