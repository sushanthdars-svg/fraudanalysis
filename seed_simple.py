#!/usr/bin/env python3
"""
Simple database seeder - runs in container with correct environment
"""

import os
import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.fraud_alert import FraudAssessment
from app.models.fraud_rule import FraudRule
from app.models.user import User
from app.core.security import hash_password
from app.core.permissions import UserRole
from app.db.base import Base

# Get database settings from environment (these come from docker-compose environment section)
# Fall back to defaults if not set
DB_USER = os.getenv('MYSQL_USER', 'fraud_user')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'fraud_password')
DB_NAME = os.getenv('MYSQL_DATABASE', 'fraud_detection_db')

# For Docker, use the service name "mysql" NOT the container name "fraud_detection_mysql"
DB_HOST = 'mysql'  # Docker service name from docker-compose.yml
DB_PORT = '3306'

# Also try reading from DATABASE_URL if available
if os.getenv('DATABASE_URL'):
    DATABASE_URL = os.getenv('DATABASE_URL')
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(f"Connecting to database using URL: {DATABASE_URL[:50]}...")
logger.info(f"Details: Host={DB_HOST}, Port={DB_PORT}, DB={DB_NAME}, User={DB_USER}")

# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    """Seed database with sample data."""
    
    # Try to connect, with retries
    max_retries = 5
    retry_count = 0
    db = None
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # Test connection
            db.execute("SELECT 1")
            logger.info("✅ Database connection successful")
            break
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Connection attempt {retry_count}/{max_retries} failed: {e}")
                time.sleep(2)
            else:
                logger.error(f"❌ Failed to connect to database after {max_retries} attempts")
                return
    
    try:
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Check if data already exists
        customer_count = db.query(Customer).count()
        if customer_count > 0:
            logger.info(f"✅ Data already exists ({customer_count} customers). Skipping seeding.")
            return
        
        logger.info("🌱 Seeding database with sample data...")
        
        # Seed customers
        logger.info("Adding customers...")
        customers = [
            Customer(name="John Smith", email="john@example.com", phone="+1-555-0101", status="active"),
            Customer(name="Jane Doe", email="jane@example.com", phone="+1-555-0102", status="active"),
            Customer(name="Robert Johnson", email="robert@example.com", phone="+1-555-0103", status="active"),
            Customer(name="Mary Williams", email="mary@example.com", phone="+1-555-0104", status="active"),
            Customer(name="Michael Brown", email="michael@example.com", phone="+1-555-0105", status="active"),
        ]
        db.add_all(customers)
        db.commit()
        logger.info(f"✅ Added {len(customers)} customers")
        
        # Seed transactions
        logger.info("Adding transactions...")
        transactions = []
        now = datetime.utcnow()
        
        txn_data = [
            (customers[0], 5000.00, "Amazon", "Electronics", 2),
            (customers[0], 3500.00, "Apple Store", "Electronics", 4),
            (customers[1], 1200.50, "Delta Airlines", "Travel", 1),
            (customers[1], 650.00, "Marriott Hotels", "Travel", 3),
            (customers[2], 2100.00, "Tokyo Dept Store", "Shopping", 6),
            (customers[2], 850.00, "Mumbai Electronics", "Electronics", 24),
            (customers[3], 200.00, "Starbucks", "Food", 0.5),
            (customers[3], 150.00, "CVS Pharmacy", "Pharmacy", 1),
            (customers[3], 3000.00, "Best Buy", "Electronics", 2),
            (customers[4], 7500.00, "Jewelry Store Dubai", "Luxury", 8),
            (customers[4], 4200.00, "Casino Online", "Gaming", 12),
            (customers[4], 2500.00, "Wire Transfer", "Banking", 18),
            (customers[0], 75.50, "Whole Foods", "Groceries", 5),
            (customers[1], 120.00, "Shell Gas Station", "Gas", 7),
            (customers[2], 95.00, "Target", "Retail", 10),
            (customers[3], 450.00, "Netflix Annual", "Subscriptions", 14),
            (customers[4], 180.00, "Gym Membership", "Fitness", 20),
        ]
        
        for i, (customer, amount, merchant, category, hours_ago) in enumerate(txn_data):
            txn = Transaction(
                transaction_id=f"TXN-{now.strftime('%Y%m%d')}-{i:04d}",
                customer_id=customer.id,
                transaction_date=now - timedelta(hours=hours_ago),
                amount=Decimal(str(amount)),
                currency="USD",
                merchant_name=merchant,
                merchant_id=f"MER-{merchant.replace(' ', '-')}",
                merchant_category=category,
                transaction_type="purchase" if category != "Banking" else "transfer",
                status="completed",
                payment_method="card",
                card_last4="4532"
            )
            transactions.append(txn)
        
        db.add_all(transactions)
        db.commit()
        logger.info(f"✅ Added {len(transactions)} transactions")
        
        # Seed fraud assessments
        logger.info("Adding fraud assessments...")
        assessments = []
        
        for txn in transactions:
            # Determine risk based on amount and merchant
            if txn.amount > 5000:
                risk_score = 75.5
                risk_category = "high"
                rules_triggered = 3
            elif txn.amount > 3000:
                risk_score = 55.0
                risk_category = "medium"
                rules_triggered = 2
            elif "Casino" in txn.merchant_name or "Jewelry" in txn.merchant_name:
                risk_score = 68.0
                risk_category = "high"
                rules_triggered = 2
            elif txn.amount > 1000:
                risk_score = 35.0
                risk_category = "medium"
                rules_triggered = 1
            else:
                risk_score = 10.0
                risk_category = "low"
                rules_triggered = 0
            
            assessment = FraudAssessment(
                transaction_id=txn.id,
                risk_score=Decimal(str(risk_score)),
                risk_category=risk_category,
                rules_triggered_count=rules_triggered,
                ml_score=Decimal(str(risk_score / 100.0)),
                ml_model_version="1.2.3",
                engine_version="1.0",
                assessment_timestamp=datetime.utcnow(),
                explanation=f"Risk assessment for {txn.merchant_name} transaction"
            )
            assessments.append(assessment)
        
        db.add_all(assessments)
        db.commit()
        logger.info(f"✅ Added {len(assessments)} fraud assessments")
        
        # Seed fraud rules
        logger.info("Adding detection rules...")
        rules = [
            FraudRule(
                name="High Transaction Amount",
                description="Transactions exceeding $5000",
                rule_type="threshold",
                condition='{"field": "amount", "operator": ">", "value": 5000}',
                threshold_value=5000,
                severity="high",
                is_enabled=True
            ),
            FraudRule(
                name="Multiple Transactions Same Hour",
                description="More than 3 transactions within 1 hour",
                rule_type="pattern",
                condition='{"field": "frequency", "operator": ">", "value": 3}',
                threshold_value=3,
                severity="medium",
                is_enabled=True
            ),
            FraudRule(
                name="International Merchant",
                description="Transaction with merchant outside USA",
                rule_type="geographical",
                condition='{"field": "merchant_country", "operator": "!=", "value": "US"}',
                threshold_value=1,
                severity="medium",
                is_enabled=True
            ),
            FraudRule(
                name="Casino or Gambling",
                description="Transactions to gambling establishments",
                rule_type="merchant_category",
                condition='{"field": "merchant_category", "operator": "contains", "value": "Casino"}',
                threshold_value=1,
                severity="high",
                is_enabled=True
            ),
            FraudRule(
                name="Luxury Merchant",
                description="Transactions to luxury merchants",
                rule_type="merchant_category",
                condition='{"field": "merchant_category", "operator": "in", "value": ["Luxury", "Jewelry"]}',
                threshold_value=1,
                severity="high",
                is_enabled=True
            ),
        ]
        
        db.add_all(rules)
        db.commit()
        logger.info(f"✅ Added {len(rules)} fraud detection rules")
        
        # Seed users
        logger.info("Adding test users...")
        users = [
            User(
                email="analyst@fraud-detection.local",
                full_name="Risk Analyst",
                password_hash=hash_password("password"),
                role=UserRole.ANALYST,
                is_active=True
            ),
            User(
                email="admin@fraud-detection.local",
                full_name="Admin User",
                password_hash=hash_password("password"),
                role=UserRole.ADMIN,
                is_active=True
            ),
            User(
                email="viewer@fraud-detection.local",
                full_name="Report Viewer",
                password_hash=hash_password("password"),
                role=UserRole.VIEWER,
                is_active=True
            ),
        ]
        
        db.add_all(users)
        db.commit()
        logger.info(f"✅ Added {len(users)} test users")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("="*60)
        logger.info(f"✓ Customers: {db.query(Customer).count()}")
        logger.info(f"✓ Transactions: {db.query(Transaction).count()}")
        logger.info(f"✓ Fraud Assessments: {db.query(FraudAssessment).count()}")
        logger.info(f"✓ Fraud Rules: {db.query(FraudRule).count()}")
        logger.info(f"✓ Users: {db.query(User).count()}")
        logger.info("="*60)
        logger.info("\n🎉 Ready to test! Data is populated in the database.")
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    seed_database()


def seed_database():
    """Seed database with sample data."""
    db = SessionLocal()
    
    try:
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Check if data already exists
        customer_count = db.query(Customer).count()
        if customer_count > 0:
            logger.info(f"✅ Data already exists ({customer_count} customers). Skipping seeding.")
            return
        
        logger.info("🌱 Seeding database with sample data...")
        
        # Seed customers
        logger.info("Adding customers...")
        customers = [
            Customer(name="John Smith", email="john@example.com", phone="+1-555-0101", status="active"),
            Customer(name="Jane Doe", email="jane@example.com", phone="+1-555-0102", status="active"),
            Customer(name="Robert Johnson", email="robert@example.com", phone="+1-555-0103", status="active"),
            Customer(name="Mary Williams", email="mary@example.com", phone="+1-555-0104", status="active"),
            Customer(name="Michael Brown", email="michael@example.com", phone="+1-555-0105", status="active"),
        ]
        db.add_all(customers)
        db.commit()
        logger.info(f"✅ Added {len(customers)} customers")
        
        # Seed transactions
        logger.info("Adding transactions...")
        transactions = []
        now = datetime.utcnow()
        
        txn_data = [
            (customers[0], 5000.00, "Amazon", "Electronics", 2),
            (customers[0], 3500.00, "Apple Store", "Electronics", 4),
            (customers[1], 1200.50, "Delta Airlines", "Travel", 1),
            (customers[1], 650.00, "Marriott Hotels", "Travel", 3),
            (customers[2], 2100.00, "Tokyo Dept Store", "Shopping", 6),
            (customers[2], 850.00, "Mumbai Electronics", "Electronics", 24),
            (customers[3], 200.00, "Starbucks", "Food", 0.5),
            (customers[3], 150.00, "CVS Pharmacy", "Pharmacy", 1),
            (customers[3], 3000.00, "Best Buy", "Electronics", 2),
            (customers[4], 7500.00, "Jewelry Store Dubai", "Luxury", 8),
            (customers[4], 4200.00, "Casino Online", "Gaming", 12),
            (customers[4], 2500.00, "Wire Transfer", "Banking", 18),
            (customers[0], 75.50, "Whole Foods", "Groceries", 5),
            (customers[1], 120.00, "Shell Gas Station", "Gas", 7),
            (customers[2], 95.00, "Target", "Retail", 10),
            (customers[3], 450.00, "Netflix Annual", "Subscriptions", 14),
            (customers[4], 180.00, "Gym Membership", "Fitness", 20),
        ]
        
        for i, (customer, amount, merchant, category, hours_ago) in enumerate(txn_data):
            txn = Transaction(
                transaction_id=f"TXN-{now.strftime('%Y%m%d')}-{i:04d}",
                customer_id=customer.id,
                transaction_date=now - timedelta(hours=hours_ago),
                amount=Decimal(str(amount)),
                currency="USD",
                merchant_name=merchant,
                merchant_id=f"MER-{merchant.replace(' ', '-')}",
                merchant_category=category,
                transaction_type="purchase" if category != "Banking" else "transfer",
                status="completed",
                payment_method="card",
                card_last4="4532"
            )
            transactions.append(txn)
        
        db.add_all(transactions)
        db.commit()
        logger.info(f"✅ Added {len(transactions)} transactions")
        
        # Seed fraud assessments
        logger.info("Adding fraud assessments...")
        assessments = []
        
        for txn in transactions:
            # Determine risk based on amount and merchant
            if txn.amount > 5000:
                risk_score = 75.5
                risk_category = "high"
                rules_triggered = 3
            elif txn.amount > 3000:
                risk_score = 55.0
                risk_category = "medium"
                rules_triggered = 2
            elif "Casino" in txn.merchant_name or "Jewelry" in txn.merchant_name:
                risk_score = 68.0
                risk_category = "high"
                rules_triggered = 2
            elif txn.amount > 1000:
                risk_score = 35.0
                risk_category = "medium"
                rules_triggered = 1
            else:
                risk_score = 10.0
                risk_category = "low"
                rules_triggered = 0
            
            assessment = FraudAssessment(
                transaction_id=txn.id,
                risk_score=Decimal(str(risk_score)),
                risk_category=risk_category,
                rules_triggered_count=rules_triggered,
                ml_score=Decimal(str(risk_score / 100.0)),
                ml_model_version="1.2.3",
                engine_version="1.0",
                assessment_timestamp=datetime.utcnow(),
                explanation=f"Risk assessment for {txn.merchant_name} transaction"
            )
            assessments.append(assessment)
        
        db.add_all(assessments)
        db.commit()
        logger.info(f"✅ Added {len(assessments)} fraud assessments")
        
        # Seed fraud rules
        logger.info("Adding detection rules...")
        rules = [
            FraudRule(
                name="High Transaction Amount",
                description="Transactions exceeding $5000",
                rule_type="threshold",
                condition='{"field": "amount", "operator": ">", "value": 5000}',
                threshold_value=5000,
                severity="high",
                is_enabled=True
            ),
            FraudRule(
                name="Multiple Transactions Same Hour",
                description="More than 3 transactions within 1 hour",
                rule_type="pattern",
                condition='{"field": "frequency", "operator": ">", "value": 3}',
                threshold_value=3,
                severity="medium",
                is_enabled=True
            ),
            FraudRule(
                name="International Merchant",
                description="Transaction with merchant outside USA",
                rule_type="geographical",
                condition='{"field": "merchant_country", "operator": "!=", "value": "US"}',
                threshold_value=1,
                severity="medium",
                is_enabled=True
            ),
            FraudRule(
                name="Casino or Gambling",
                description="Transactions to gambling establishments",
                rule_type="merchant_category",
                condition='{"field": "merchant_category", "operator": "contains", "value": "Casino"}',
                threshold_value=1,
                severity="high",
                is_enabled=True
            ),
            FraudRule(
                name="Luxury Merchant",
                description="Transactions to luxury merchants",
                rule_type="merchant_category",
                condition='{"field": "merchant_category", "operator": "in", "value": ["Luxury", "Jewelry"]}',
                threshold_value=1,
                severity="high",
                is_enabled=True
            ),
        ]
        
        db.add_all(rules)
        db.commit()
        logger.info(f"✅ Added {len(rules)} fraud detection rules")
        
        # Seed users
        logger.info("Adding test users...")
        users = [
            User(
                email="analyst@fraud-detection.local",
                full_name="Risk Analyst",
                password_hash=hash_password("password"),
                role=UserRole.ANALYST,
                is_active=True
            ),
            User(
                email="admin@fraud-detection.local",
                full_name="Admin User",
                password_hash=hash_password("password"),
                role=UserRole.ADMIN,
                is_active=True
            ),
            User(
                email="viewer@fraud-detection.local",
                full_name="Report Viewer",
                password_hash=hash_password("password"),
                role=UserRole.VIEWER,
                is_active=True
            ),
        ]
        
        db.add_all(users)
        db.commit()
        logger.info(f"✅ Added {len(users)} test users")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("="*60)
        logger.info(f"✓ Customers: {db.query(Customer).count()}")
        logger.info(f"✓ Transactions: {db.query(Transaction).count()}")
        logger.info(f"✓ Fraud Assessments: {db.query(FraudAssessment).count()}")
        logger.info(f"✓ Fraud Rules: {db.query(FraudRule).count()}")
        logger.info(f"✓ Users: {db.query(User).count()}")
        logger.info("="*60)
        logger.info("\n🎉 Ready to test! Data is populated in the database.")
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
