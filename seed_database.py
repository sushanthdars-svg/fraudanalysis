#!/usr/bin/env python3
"""
Seed database with sample data for testing.
This script populates transactions, fraud alerts, detection rules, and test data.
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import logging

# Add app to path
sys.path.insert(0, '/app')

from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.fraud_alert import FraudAssessment, TriggeredRule
from app.models.fraud_rule import FraudRule
from app.models.user import User
from app.core.security import hash_password
from app.core.permissions import UserRole
from app.db.base import Base
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Database connection
DATABASE_URL = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_engine(DATABASE_URL)


def seed_customers(db: Session):
    """Add sample customers."""
    logger.info("Seeding customers...")
    
    customers = [
        {"name": "John Smith", "email": "john@example.com", "phone": "+1-555-0101"},
        {"name": "Jane Doe", "email": "jane@example.com", "phone": "+1-555-0102"},
        {"name": "Robert Johnson", "email": "robert@example.com", "phone": "+1-555-0103"},
        {"name": "Mary Williams", "email": "mary@example.com", "phone": "+1-555-0104"},
        {"name": "Michael Brown", "email": "michael@example.com", "phone": "+1-555-0105"},
    ]
    
    for cust_data in customers:
        existing = db.query(Customer).filter_by(email=cust_data['email']).first()
        if not existing:
            customer = Customer(
                name=cust_data['name'],
                email=cust_data['email'],
                phone=cust_data['phone'],
                status='active'
            )
            db.add(customer)
    
    db.commit()
    logger.info("✅ Customers seeded")


def seed_transactions(db: Session):
    """Add sample transactions."""
    logger.info("Seeding transactions...")
    
    customers = db.query(Customer).all()
    if not customers:
        logger.warning("No customers found. Skipping transactions.")
        return
    
    transactions_data = [
        # Recent high-value transactions
        {"customer_id": customers[0].id, "amount": 5000.00, "merchant": "Amazon", "category": "Electronics", "type": "purchase", "status": "completed", "hours_ago": 2},
        {"customer_id": customers[0].id, "amount": 3500.00, "merchant": "Apple Store", "category": "Electronics", "type": "purchase", "status": "completed", "hours_ago": 4},
        {"customer_id": customers[1].id, "amount": 1200.50, "merchant": "Delta Airlines", "category": "Travel", "type": "purchase", "status": "completed", "hours_ago": 1},
        {"customer_id": customers[1].id, "amount": 650.00, "merchant": "Marriott Hotels", "category": "Travel", "type": "purchase", "status": "completed", "hours_ago": 3},
        
        # International transactions (potential fraud indicators)
        {"customer_id": customers[2].id, "amount": 2100.00, "merchant": "Tokyo Dept Store", "category": "Shopping", "type": "purchase", "status": "completed", "hours_ago": 6},
        {"customer_id": customers[2].id, "amount": 850.00, "merchant": "Mumbai Electronics", "category": "Electronics", "type": "purchase", "status": "completed", "hours_ago": 24},
        
        # Multiple transactions from same customer
        {"customer_id": customers[3].id, "amount": 200.00, "merchant": "Starbucks", "category": "Food", "type": "purchase", "status": "completed", "hours_ago": 0.5},
        {"customer_id": customers[3].id, "amount": 150.00, "merchant": "CVS Pharmacy", "category": "Pharmacy", "type": "purchase", "status": "completed", "hours_ago": 1},
        {"customer_id": customers[3].id, "amount": 3000.00, "merchant": "Best Buy", "category": "Electronics", "type": "purchase", "status": "completed", "hours_ago": 2},
        
        # Unusual transactions (fraud candidates)
        {"customer_id": customers[4].id, "amount": 7500.00, "merchant": "Jewelry Store Dubai", "category": "Luxury", "type": "purchase", "status": "completed", "hours_ago": 8},
        {"customer_id": customers[4].id, "amount": 4200.00, "merchant": "Casino Online", "category": "Gaming", "type": "purchase", "status": "completed", "hours_ago": 12},
        {"customer_id": customers[4].id, "amount": 2500.00, "merchant": "Wire Transfer International", "category": "Banking", "type": "transfer", "status": "completed", "hours_ago": 18},
        
        # Normal transactions
        {"customer_id": customers[0].id, "amount": 75.50, "merchant": "Whole Foods", "category": "Groceries", "type": "purchase", "status": "completed", "hours_ago": 5},
        {"customer_id": customers[1].id, "amount": 120.00, "merchant": "Shell Gas Station", "category": "Gas", "type": "purchase", "status": "completed", "hours_ago": 7},
        {"customer_id": customers[2].id, "amount": 95.00, "merchant": "Target", "category": "Retail", "type": "purchase", "status": "completed", "hours_ago": 10},
        {"customer_id": customers[3].id, "amount": 450.00, "merchant": "Netflix Annual", "category": "Subscriptions", "type": "purchase", "status": "completed", "hours_ago": 14},
        {"customer_id": customers[4].id, "amount": 180.00, "merchant": "Gym Membership", "category": "Fitness", "type": "purchase", "status": "completed", "hours_ago": 20},
    ]
    
    for i, txn_data in enumerate(transactions_data):
        txn_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d')}-{i:04d}"
        existing = db.query(Transaction).filter_by(transaction_id=txn_id).first()
        
        if not existing:
            transaction = Transaction(
                transaction_id=txn_id,
                customer_id=txn_data['customer_id'],
                transaction_date=datetime.utcnow() - timedelta(hours=txn_data['hours_ago']),
                amount=Decimal(str(txn_data['amount'])),
                currency="USD",
                merchant_name=txn_data['merchant'],
                merchant_id=f"MER-{txn_data['merchant'].replace(' ', '-')}",
                merchant_category=txn_data['category'],
                transaction_type=txn_data['type'],
                status=txn_data['status'],
                payment_method="card",
                card_last4="4532"
            )
            db.add(transaction)
    
    db.commit()
    logger.info("✅ Transactions seeded")


def seed_fraud_assessments(db: Session):
    """Add fraud assessments for transactions."""
    logger.info("Seeding fraud assessments...")
    
    transactions = db.query(Transaction).all()
    
    for txn in transactions:
        existing = db.query(FraudAssessment).filter_by(transaction_id=txn.id).first()
        if not existing:
            # Determine risk based on amount and merchant
            if txn.amount > 5000:
                risk_score = 75.5
                risk_category = "high"
                rules_triggered = 3
            elif txn.amount > 3000:
                risk_score = 55.0
                risk_category = "medium"
                rules_triggered = 2
            elif "Casino" in txn.merchant_name or "Jewelry" in txn.merchant_name or "Dubai" in txn.merchant_name:
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
                explanation=f"Risk assessment for {txn.merchant_name} transaction of ${txn.amount}"
            )
            db.add(assessment)
    
    db.commit()
    logger.info("✅ Fraud assessments seeded")


def seed_fraud_rules(db: Session):
    """Add fraud detection rules."""
    logger.info("Seeding fraud detection rules...")
    
    rules_data = [
        {
            "name": "High Transaction Amount",
            "description": "Transactions exceeding $5000",
            "rule_type": "threshold",
            "condition": '{"field": "amount", "operator": ">", "value": 5000}',
            "threshold_value": 5000,
            "severity": "high",
            "enabled": True
        },
        {
            "name": "Multiple Transactions Same Hour",
            "description": "More than 3 transactions within 1 hour from same customer",
            "rule_type": "pattern",
            "condition": '{"field": "frequency", "operator": ">", "value": 3, "window": 3600}',
            "threshold_value": 3,
            "severity": "medium",
            "enabled": True
        },
        {
            "name": "International Merchant",
            "description": "Transaction with merchant outside USA",
            "rule_type": "geographical",
            "condition": '{"field": "merchant_country", "operator": "!=", "value": "US"}',
            "threshold_value": 1,
            "severity": "medium",
            "enabled": True
        },
        {
            "name": "Casino or Gambling",
            "description": "Transactions to gambling establishments",
            "rule_type": "merchant_category",
            "condition": '{"field": "merchant_category", "operator": "contains", "value": "Casino"}',
            "threshold_value": 1,
            "severity": "high",
            "enabled": True
        },
        {
            "name": "Unusual Merchant Category",
            "description": "Transaction to luxury or high-risk merchants",
            "rule_type": "merchant_category",
            "condition": '{"field": "merchant_category", "operator": "in", "value": ["Luxury", "Gaming", "Jewelry"]}',
            "threshold_value": 1,
            "severity": "high",
            "enabled": True
        },
        {
            "name": "Card-Not-Present High Value",
            "description": "High-value CNP transaction",
            "rule_type": "transaction_method",
            "condition": '{"field": "payment_method", "operator": "==", "value": "online"}',
            "threshold_value": 2000,
            "severity": "medium",
            "enabled": True
        },
        {
            "name": "Rapid Geographical Movement",
            "description": "Transactions in different cities within short timeframe",
            "rule_type": "geographical",
            "condition": '{"field": "distance", "operator": ">", "value": 500}',
            "threshold_value": 500,
            "severity": "high",
            "enabled": True
        },
        {
            "name": "Velocity Check - Daily Limit",
            "description": "Daily spending exceeds $10,000",
            "rule_type": "velocity",
            "condition": '{"field": "daily_amount", "operator": ">", "value": 10000}',
            "threshold_value": 10000,
            "severity": "high",
            "enabled": True
        }
    ]
    
    for rule_data in rules_data:
        existing = db.query(FraudRule).filter_by(name=rule_data['name']).first()
        if not existing:
            rule = FraudRule(
                name=rule_data['name'],
                description=rule_data['description'],
                rule_type=rule_data['rule_type'],
                condition=rule_data['condition'],
                threshold_value=rule_data['threshold_value'],
                severity=rule_data['severity'],
                is_enabled=rule_data['enabled'],
                created_at=datetime.utcnow()
            )
            db.add(rule)
    
    db.commit()
    logger.info("✅ Fraud rules seeded")


def seed_users(db: Session):
    """Add test users."""
    logger.info("Seeding test users...")
    
    users_data = [
        {
            "email": "analyst@fraud-detection.local",
            "full_name": "Risk Analyst",
            "password": "password",
            "role": UserRole.ANALYST
        },
        {
            "email": "admin@fraud-detection.local",
            "full_name": "Admin User",
            "password": "password",
            "role": UserRole.ADMIN
        },
        {
            "email": "viewer@fraud-detection.local",
            "full_name": "Report Viewer",
            "password": "password",
            "role": UserRole.VIEWER
        }
    ]
    
    for user_data in users_data:
        existing = db.query(User).filter_by(email=user_data['email']).first()
        if not existing:
            user = User(
                email=user_data['email'],
                full_name=user_data['full_name'],
                password_hash=hash_password(user_data['password']),
                role=user_data['role'],
                is_active=True
            )
            db.add(user)
    
    db.commit()
    logger.info("✅ Test users seeded")


def main():
    """Execute all seeding operations."""
    logger.info("=" * 60)
    logger.info("🌱 Starting database seeding...")
    logger.info("=" * 60)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = __import__('sqlalchemy.orm', fromlist=['sessionmaker']).sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    db = SessionLocal()
    
    try:
        seed_users(db)
        seed_customers(db)
        seed_transactions(db)
        seed_fraud_assessments(db)
        seed_fraud_rules(db)
        
        logger.info("=" * 60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("\n📊 Sample Data Summary:")
        logger.info(f"   - Customers: {db.query(Customer).count()}")
        logger.info(f"   - Transactions: {db.query(Transaction).count()}")
        logger.info(f"   - Fraud Assessments: {db.query(FraudAssessment).count()}")
        logger.info(f"   - Fraud Rules: {db.query(FraudRule).count()}")
        logger.info(f"   - Users: {db.query(User).count()}")
        logger.info("\n✨ Ready to test! Visit: http://localhost:3000")
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
