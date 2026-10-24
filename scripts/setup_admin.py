#!/usr/bin/env python
"""Script to create initial admin user."""

import os
import sys
import logging
from pathlib import Path
import getpass
from datetime import datetime

# Add the project root, not the scripts directory, so direct script execution can
# resolve the app package both locally and in the API container.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.core.config import get_settings
from app.core.security import hash_password

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin_user(
    email: str,
    password: str,
    full_name: str = None,
    prompt_for_input: bool = True
) -> bool:
    """
    Create an admin user in the database.
    
    Args:
        email: Admin email address
        password: Admin password
        full_name: Admin full name
        prompt_for_input: Whether to prompt for missing values
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate email format
        if "@" not in email or "." not in email.split("@")[1]:
            logger.error("❌ Invalid email format")
            return False
        
        # Create database connection
        engine = create_engine(get_settings().database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            logger.error(f"❌ User with email '{email}' already exists")
            session.close()
            return False
        
        # Validate password strength
        if len(password) < 8:
            logger.error("❌ Password must be at least 8 characters long")
            session.close()
            return False
        
        # Create new admin user
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name or email.split("@")[0],
            role="admin",
            is_active=True
        )
        
        session.add(admin_user)
        session.commit()
        
        logger.info(f"✅ Admin user created successfully!")
        logger.info(f"   Email: {email}")
        logger.info(f"   Full Name: {admin_user.full_name}")
        logger.info(f"   Role: {admin_user.role}")
        logger.info(f"   Created At: {admin_user.created_at}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {str(e)}")
        return False


def prompt_for_admin_details() -> dict:
    """Prompt user for admin details interactively."""
    print("\n" + "="*50)
    print("CREATE ADMIN USER")
    print("="*50)
    
    while True:
        email = input("\nEmail address: ").strip()
        if "@" in email and "." in email.split("@")[1]:
            break
        print("❌ Invalid email format. Please try again.")
    
    while True:
        password = getpass.getpass("Password (min 8 characters): ")
        if len(password) >= 8:
            password_confirm = getpass.getpass("Confirm password: ")
            if password == password_confirm:
                break
            print("❌ Passwords do not match. Please try again.")
        else:
            print("❌ Password must be at least 8 characters. Please try again.")
    
    full_name = input("Full name (optional): ").strip() or None
    
    return {
        "email": email,
        "password": password,
        "full_name": full_name
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Admin User")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password")
    parser.add_argument("--full-name", help="Admin full name")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for details interactively"
    )
    
    args = parser.parse_args()
    
    if args.interactive or not args.email:
        details = prompt_for_admin_details()
        success = create_admin_user(
            email=details["email"],
            password=details["password"],
            full_name=details["full_name"],
            prompt_for_input=False
        )
    else:
        if not args.password:
            print("❌ Error: Password is required when email is provided")
            sys.exit(1)
        
        success = create_admin_user(
            email=args.email,
            password=args.password,
            full_name=args.full_name,
            prompt_for_input=False
        )
    
    sys.exit(0 if success else 1)
