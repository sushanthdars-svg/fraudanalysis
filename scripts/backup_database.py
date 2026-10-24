#!/usr/bin/env python
"""Script to backup MySQL database."""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.absolute().parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_database_url(url: str) -> dict:
    """Parse database URL to extract connection details."""
    parsed = urlparse(url)
    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "database": parsed.path.lstrip("/")
    }


def backup_database(
    output_dir: str = "backups",
    compress: bool = True,
    retention_days: int = 7
) -> bool:
    """
    Backup MySQL database.
    
    Args:
        output_dir: Directory to store backups
        compress: Whether to compress the backup
        retention_days: Number of days to keep backups
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse database connection details
        db_config = parse_database_url(settings.DATABASE_URL)
        
        # Create output directory
        backup_dir = Path(output_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{db_config['database']}_{timestamp}.sql"
        
        if compress:
            backup_file = backup_file.with_suffix(".sql.gz")
        
        logger.info(f"Starting database backup to: {backup_file}")
        
        # Build mysqldump command
        cmd = [
            "mysqldump",
            f"--user={db_config['user']}",
            f"--password={db_config['password']}",
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            "--single-transaction",
            "--quick",
            "--lock-tables=false",
            db_config['database']
        ]
        
        if compress:
            # Pipe to gzip
            cmd_str = " ".join(cmd) + f" | gzip > {backup_file}"
            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
        else:
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Backup failed: {result.stderr}")
            return False
        
        # Verify backup
        if not backup_file.exists():
            logger.error("❌ Backup file was not created")
            return False
        
        backup_size = backup_file.stat().st_size
        logger.info(f"✅ Backup completed successfully!")
        logger.info(f"   File: {backup_file}")
        logger.info(f"   Size: {backup_size / (1024*1024):.2f} MB")
        
        # Clean up old backups
        cleanup_old_backups(backup_dir, retention_days)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return False


def cleanup_old_backups(backup_dir: Path, retention_days: int = 7) -> None:
    """Delete backups older than retention period."""
    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for backup_file in backup_dir.glob("backup_*.sql*"):
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"Deleted old backup: {backup_file.name}")
        
    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {str(e)}")


def restore_backup(backup_file: str) -> bool:
    """
    Restore database from backup file.
    
    Args:
        backup_file: Path to backup file (compressed or uncompressed)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error(f"❌ Backup file not found: {backup_file}")
            return False
        
        # Parse database connection details
        db_config = parse_database_url(settings.DATABASE_URL)
        
        logger.info(f"Starting restore from: {backup_file}")
        
        # Build mysql command
        cmd = [
            "mysql",
            f"--user={db_config['user']}",
            f"--password={db_config['password']}",
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            db_config['database']
        ]
        
        if str(backup_file).endswith('.gz'):
            # Decompress on the fly
            cmd_str = f"gunzip < {backup_file} | " + " ".join(cmd)
            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
        else:
            with open(backup_file, 'r') as f:
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Restore failed: {result.stderr}")
            return False
        
        logger.info("✅ Restore completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Restore failed: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Backup Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument(
        "--output-dir",
        default="backups",
        help="Directory to store backups"
    )
    backup_parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress the backup"
    )
    backup_parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Keep backups for N days (default: 7)"
    )
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_file", help="Path to backup file")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument(
        "--output-dir",
        default="backups",
        help="Directory containing backups"
    )
    
    args = parser.parse_args()
    
    if args.command == "backup":
        success = backup_database(
            output_dir=args.output_dir,
            compress=not args.no_compress,
            retention_days=args.retention_days
        )
        sys.exit(0 if success else 1)
    elif args.command == "restore":
        success = restore_backup(args.backup_file)
        sys.exit(0 if success else 1)
    elif args.command == "list":
        backup_dir = Path(args.output_dir)
        if backup_dir.exists():
            print(f"\nAvailable backups in {backup_dir}:")
            for backup_file in sorted(backup_dir.glob("backup_*.sql*")):
                size = backup_file.stat().st_size / (1024*1024)
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                print(f"  {backup_file.name} ({size:.2f} MB) - {mtime}")
        else:
            print(f"No backups directory found at {backup_dir}")
    else:
        parser.print_help()
        sys.exit(1)
