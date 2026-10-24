#!/usr/bin/env python
"""Script to run database migrations using Alembic."""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migrations(revision: str = "head", direction: str = "upgrade") -> bool:
    """
    Run database migrations.
    
    Args:
        revision: Target revision (default: "head" - latest)
        direction: Direction of migration - "upgrade" or "downgrade"
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting database migration to {revision}...")
        
        # Get Alembic config
        alembic_cfg = Config(os.path.join(project_root, "migrations", "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        alembic_cfg.set_main_option("script_location", os.path.join(project_root, "migrations"))
        
        if direction == "upgrade":
            command.upgrade(alembic_cfg, revision)
            logger.info(f"✅ Successfully upgraded to revision: {revision}")
        elif direction == "downgrade":
            command.downgrade(alembic_cfg, revision)
            logger.info(f"✅ Successfully downgraded to revision: {revision}")
        else:
            logger.error(f"Invalid direction: {direction}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False


def get_migration_history() -> bool:
    """Display migration history."""
    try:
        logger.info("Fetching migration history...")
        
        alembic_cfg = Config(os.path.join(project_root, "migrations", "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        alembic_cfg.set_main_option("script_location", os.path.join(project_root, "migrations"))
        
        command.history(alembic_cfg)
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}")
        return False


def show_migration_status() -> bool:
    """Show current migration status."""
    try:
        logger.info("Fetching migration status...")
        
        alembic_cfg = Config(os.path.join(project_root, "migrations", "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        alembic_cfg.set_main_option("script_location", os.path.join(project_root, "migrations"))
        
        command.current(alembic_cfg)
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch status: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database to target revision")
    upgrade_parser.add_argument(
        "--revision", 
        default="head", 
        help="Target revision (default: head)"
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database to previous revision")
    downgrade_parser.add_argument(
        "revision", 
        help="Target revision to downgrade to"
    )
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    # Current command
    subparsers.add_parser("current", help="Show current migration status")
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        success = run_migrations(args.revision, "upgrade")
        sys.exit(0 if success else 1)
    elif args.command == "downgrade":
        success = run_migrations(args.revision, "downgrade")
        sys.exit(0 if success else 1)
    elif args.command == "history":
        success = get_migration_history()
        sys.exit(0 if success else 1)
    elif args.command == "current":
        success = show_migration_status()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)
