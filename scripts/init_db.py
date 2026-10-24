#!/usr/bin/env python3
"""
Database initialization script.
Creates database, user, and tables for the fraud detection system.
"""

import mysql.connector
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.db.base import Base
from app.db.database import engine


def main():
    """Main initialization flow."""
    logger.info("=" * 60)
    logger.info("Database Initialization Script")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    # Get MySQL credentials
    admin_user = input(f"\nMySQL admin user (default 'root'): ").strip() or "root"
    admin_password = input("MySQL admin password: ").strip()
    
    # Confirm database settings
    logger.info(f"\nDatabase Configuration:")
    logger.info(f"  Host: {settings.db_host}")
    logger.info(f"  Database: {settings.db_name}")
    logger.info(f"  User: {settings.db_user}")
    
    confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        logger.info("Cancelled.")
        return
    
    try:
        # Connect as admin
        logger.info("\nConnecting to MySQL as admin...")
        connection = mysql.connector.connect(
            host=settings.db_host,
            user=admin_user,
            password=admin_password,
            autocommit=False
        )
        
        cursor = connection.cursor()
        
        # Create database
        logger.info(f"Creating database '{settings.db_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        # Create user
        logger.info(f"Creating user '{settings.db_user}'@'localhost'...")
        cursor.execute(f"DROP USER IF EXISTS '{settings.db_user}'@'localhost';")
        cursor.execute(f"CREATE USER '{settings.db_user}'@'localhost' IDENTIFIED BY '{settings.db_password}';")
        
        # Grant permissions
        logger.info(f"Granting permissions to '{settings.db_user}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{settings.db_name}`.* TO '{settings.db_user}'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("✓ Database and user created successfully!")
        
        # Create tables
        logger.info("\nCreating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables created successfully!")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Database initialization completed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
