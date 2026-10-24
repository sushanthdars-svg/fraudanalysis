#!/usr/bin/env python
"""Script to reset development database with sample data."""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random
import string

# Add project root to path
project_root = Path(__file__).parent.absolute().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import (
    User, Customer, Transaction, FraudRule, Alert, InvestigationCase, AuditLog
)
from app.database import Base
from app.core.config import settings
from app.core.security import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_random_string(length: int = 10) -> str:
    """Generate random string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def reset_database(confirm: bool = False) -> bool:
    """
    Reset development database and load sample data.
    
    Args:
        confirm: Whether to skip confirmation prompt
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not confirm:
            print("\n" + "="*60)
            print("⚠️  WARNING: This will DELETE ALL DATA from the database!")
            print("="*60)
            response = input("\nType 'RESET' to confirm: ").strip().upper()
            if response != "RESET":
                print("❌ Reset cancelled")
                return False
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(engine)
        
        logger.info("Creating all tables...")
        Base.metadata.create_all(engine)
        
        logger.info("Loading sample data...")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test users
        users = [
            User(
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                full_name="Admin User",
                role="admin",
                is_active=True
            ),
            User(
                email="analyst@example.com",
                password_hash=get_password_hash("analyst123"),
                full_name="John Analyst",
                role="analyst",
                is_active=True
            ),
            User(
                email="investigator@example.com",
                password_hash=get_password_hash("investigator123"),
                full_name="Jane Investigator",
                role="investigator",
                is_active=True
            ),
            User(
                email="viewer@example.com",
                password_hash=get_password_hash("viewer123"),
                full_name="Bob Viewer",
                role="viewer",
                is_active=True
            ),
        ]
        session.add_all(users)
        session.flush()
        
        logger.info(f"  ✓ Created {len(users)} test users")
        
        # Create test customers
        customers = []
        for i in range(20):
            customer = Customer(
                customer_id=f"CUST{1000+i:04d}",
                full_name=f"Test Customer {i+1}",
                email=f"customer{i+1}@example.com",
                phone=f"+1{random.randint(2000000000, 9999999999)}",
                address=f"{random.randint(1, 999)} Test Street",
                date_of_birth=datetime.now().date() - timedelta(days=random.randint(8000, 25000)),
                kyc_verified=True,
                kyc_verification_date=datetime.now() - timedelta(days=random.randint(1, 365)),
                account_status="active",
                risk_profile=random.choice(["low", "medium", "high"])
            )
            customers.append(customer)
        
        session.add_all(customers)
        session.flush()
        
        logger.info(f"  ✓ Created {len(customers)} test customers")
        
        # Create test transactions
        transactions = []
        for customer in customers:
            for _ in range(random.randint(3, 10)):
                transaction = Transaction(
                    transaction_id=f"TXN{generate_random_string(10).upper()}",
                    customer_id=customer.id,
                    merchant_id=f"MERCH{random.randint(1000, 9999)}",
                    transaction_date=datetime.now() - timedelta(days=random.randint(0, 30)),
                    amount=round(random.uniform(10, 5000), 2),
                    currency="USD",
                    transaction_type=random.choice(["purchase", "withdrawal", "transfer", "deposit"]),
                    status=random.choice(["completed", "pending", "failed"]),
                    location=random.choice(["US", "UK", "CA", "AU"]),
                    ip_address=f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
                    device_id=f"DEVICE{generate_random_string(8).upper()}",
                    mcc_code=f"{random.randint(1000, 9999)}"
                )
                transactions.append(transaction)
        
        session.add_all(transactions)
        session.flush()
        
        logger.info(f"  ✓ Created {len(transactions)} test transactions")
        
        # Create fraud rules
        fraud_rules = [
            FraudRule(
                rule_name="High Amount Transaction",
                rule_type="amount",
                description="Alert on transactions > $5000",
                rule_logic={"threshold": 5000, "operator": "gt"},
                severity="high",
                is_active=True,
                priority=1
            ),
            FraudRule(
                rule_name="Unusual Location",
                rule_type="location",
                description="Alert on transactions from unusual locations",
                rule_logic={"trusted_locations": ["US", "CA"], "operator": "not_in"},
                severity="medium",
                is_active=True,
                priority=2
            ),
            FraudRule(
                rule_name="Multiple Failed Attempts",
                rule_type="behavior",
                description="Alert on multiple failed transactions",
                rule_logic={"failed_count": 3, "time_window_hours": 1},
                severity="high",
                is_active=True,
                priority=1
            ),
            FraudRule(
                rule_name="Velocity Check",
                rule_type="velocity",
                description="Alert on high transaction velocity",
                rule_logic={"transaction_count": 5, "time_window_hours": 1},
                severity="medium",
                is_active=True,
                priority=2
            ),
        ]
        session.add_all(fraud_rules)
        session.flush()
        
        logger.info(f"  ✓ Created {len(fraud_rules)} fraud rules")
        
        # Create test alerts
        alerts = []
        for transaction in transactions[:10]:
            alert = Alert(
                alert_id=f"ALERT{generate_random_string(10).upper()}",
                transaction_id=transaction.id,
                customer_id=transaction.customer_id,
                fraud_rule_id=random.choice(fraud_rules).id,
                alert_type=random.choice(["velocity", "amount", "location", "behavior"]),
                severity=random.choice(["low", "medium", "high", "critical"]),
                risk_score=round(random.uniform(0, 100), 2),
                status=random.choice(["open", "investigating", "closed"]),
                assigned_to_id=random.choice(users).id if random.random() > 0.3 else None,
                description="Test alert for fraud detection"
            )
            alerts.append(alert)
        
        session.add_all(alerts)
        session.flush()
        
        logger.info(f"  ✓ Created {len(alerts)} test alerts")
        
        # Create test investigation cases
        cases = []
        for alert in alerts[:5]:
            case = InvestigationCase(
                case_id=f"CASE{generate_random_string(10).upper()}",
                alert_id=alert.id,
                customer_id=alert.customer_id,
                assigned_to_id=random.choice(users).id,
                case_status=random.choice(["open", "investigating", "closed", "escalated"]),
                case_type=random.choice(["fraud", "suspicious", "review"]),
                priority=random.choice(["low", "medium", "high"]),
                notes="Test investigation case"
            )
            cases.append(case)
        
        session.add_all(cases)
        session.flush()
        
        logger.info(f"  ✓ Created {len(cases)} investigation cases")
        
        # Create audit logs
        audit_logs = [
            AuditLog(
                actor_id=users[0].id,
                action="reset_database",
                target_type="database",
                details="Database reset for development"
            ),
            AuditLog(
                actor_id=users[0].id,
                action="load_sample_data",
                target_type="database",
                details="Loaded sample data for testing"
            )
        ]
        session.add_all(audit_logs)
        
        # Commit all changes
        session.commit()
        
        logger.info("✅ Database reset completed successfully!")
        logger.info("\nTest Credentials:")
        logger.info("  Admin:       admin@example.com / admin123")
        logger.info("  Analyst:     analyst@example.com / analyst123")
        logger.info("  Investigator: investigator@example.com / investigator123")
        logger.info("  Viewer:      viewer@example.com / viewer123")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Reset failed: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset Development Database")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    
    args = parser.parse_args()
    
    success = reset_database(confirm=args.confirm)
    sys.exit(0 if success else 1)
