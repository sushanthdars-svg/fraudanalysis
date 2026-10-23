#!/usr/bin/env python3
"""
Direct data population script - populates missing data in database
"""

import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardcoded connection string
DATABASE_URL = "mysql+pymysql://fraud_user:fraud_password@localhost:3307/fraud_detection_db"

# Create engine and session  
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.fraud_alert import FraudAssessment
from app.models.fraud_rule import FraudRule
from app.models.user import User
from app.core.security import hash_password
from app.core.permissions import UserRole

def populate_data():
    """Populate database with sample data."""
    db = SessionLocal()
    
    try:
        logger.info("Connecting to database...")
        
        # Check what data already exists
        customer_count = db.query(Customer).count()
        transaction_count = db.query(Transaction).count()
        rule_count = db.query(FraudRule).count()
        assessment_count = db.query(FraudAssessment).count()
        
        logger.info(f"Current data: {customer_count} customers, {transaction_count} transactions, {rule_count} rules, {assessment_count} assessments")
        
        if customer_count > 0 and transaction_count > 0 and rule_count > 0 and assessment_count > 0:
            logger.info(f"✅ All data already exists. Complete!")
            return
        
        logger.info("🌱 Populating missing data...")
        
        # Only populate fraud rules if they don't exist
        if rule_count == 0:
            logger.info("Adding detection rules...")
            rules = [
                FraudRule(
                    rule_id="R001",
                    name="High Transaction Amount",
                    description="Transactions exceeding $5000",
                    rule_type="high_value",
                    threshold_value=Decimal("5000"),
                    threshold_unit="amount",
                    severity="high",
                    risk_weight=Decimal("25"),
                    is_enabled=True
                ),
                FraudRule(
                    rule_id="R002",
                    name="Multiple Transactions Same Hour",
                    description="More than 3 transactions within 1 hour",
                    rule_type="velocity",
                    threshold_value=Decimal("3"),
                    threshold_unit="count",
                    severity="medium",
                    risk_weight=Decimal("20"),
                    is_enabled=True
                ),
                FraudRule(
                    rule_id="R003",
                    name="International Merchant",
                    description="Transaction with merchant outside USA",
                    rule_type="geographic",
                    threshold_value=Decimal("1"),
                    threshold_unit="count",
                    severity="medium",
                    risk_weight=Decimal("15"),
                    is_enabled=True
                ),
                FraudRule(
                    rule_id="R004",
                    name="Casino or Gambling",
                    description="Transactions to gambling establishments",
                    rule_type="merchant_category",
                    threshold_value=Decimal("1"),
                    threshold_unit="count",
                    severity="high",
                    risk_weight=Decimal("30"),
                    is_enabled=True
                ),
                FraudRule(
                    rule_id="R005",
                    name="Luxury Merchant",
                    description="Transactions to luxury merchants",
                    rule_type="merchant_category",
                    threshold_value=Decimal("1"),
                    threshold_unit="count",
                    severity="high",
                    risk_weight=Decimal("25"),
                    is_enabled=True
                ),
            ]
            
            db.add_all(rules)
            db.commit()
            logger.info(f"✅ Added {len(rules)} fraud detection rules")
        else:
            logger.info(f"⏭️  Rules already exist ({rule_count}). Skipping rules creation.")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Data population completed!")
        logger.info("="*60)
        logger.info(f"✓ Customers: {db.query(Customer).count()}")
        logger.info(f"✓ Transactions: {db.query(Transaction).count()}")
        logger.info(f"✓ Fraud Assessments: {db.query(FraudAssessment).count()}")
        logger.info(f"✓ Fraud Rules: {db.query(FraudRule).count()}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    populate_data()
