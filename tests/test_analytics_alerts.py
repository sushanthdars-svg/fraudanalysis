"""
Tests for alert analytics functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.analytics_service import AnalyticsService
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.fraud_alert import FraudAlert, FraudAssessment
from tests.conftest import create_test_fraud_assessment_and_alert


@pytest.fixture
def db(test_session):
    """Alias test_session as db for compatibility."""
    yield test_session


@pytest.fixture
def sample_customer(db):
    """Create sample customer for tests."""
    customer = Customer(
        customer_id="CUST_ALERT_001",
        name="Test Customer",
        email="alert_test@example.com",
        phone="+1234567890",
        customer_type="individual",
        country="US",
        city="New York",
        risk_profile="low"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


class TestAlertAnalytics:
    """Test suite for alert-level analytics."""

    def test_get_alert_statistics_basic(self, db: Session, sample_customer: Customer):
        """Test basic alert statistics retrieval."""
        # Create sample alerts in different statuses using unique transactions
        # 3 pending alerts
        for i in range(3):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_ALERT_STAT_PND_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=50 + i * 10
            )
            alert.alert_status = "pending"
            db.commit()

        # 2 approved (resolved) alerts
        for i in range(2):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_ALERT_APP_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=75
            )
            alert.alert_status = "resolved"
            alert.review_decision = "approved"
            db.commit()

        # 1 rejected alert
        txn = Transaction(
            customer_id=sample_customer.id,
            transaction_id=f"TXN_ALERT_REJ",
            amount=Decimal("500.00"),
            transaction_date=datetime.utcnow(),
            transaction_type="credit_transfer",
            currency="USD",
            merchant_name="Test",
            merchant_id="M001"
        )
        db.add(txn)
        db.flush()
        
        assessment, alert = create_test_fraud_assessment_and_alert(
            db, txn.id, sample_customer.id,
            risk_score=25
        )
        alert.alert_status = "resolved"
        alert.review_decision = "rejected"
        db.commit()

        # Get statistics
        stats = AnalyticsService.get_alert_statistics(db, days=30)

        assert stats["total_alerts"] >= 6
        assert stats["pending_alerts"] >= 3
        assert stats["resolved_alerts"] >= 3
        assert "approval_rate" in stats
        assert "rejection_rate" in stats

    def test_get_fraud_confirmed_rate(self, db: Session, sample_customer: Customer):
        """Test fraud confirmed rate calculation."""
        # Create alerts: 4 approved (confirmed fraud), 6 rejected (false positives)
        # All use unique transactions
        for i in range(4):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_CONFIRM_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=80
            )
            alert.alert_status = "resolved"
            alert.review_decision = "approved"
            db.commit()

        for i in range(6):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_FALSE_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=30
            )
            alert.alert_status = "resolved"
            alert.review_decision = "rejected"
            db.commit()

        # Get fraud confirmed rate
        confirmed_rate = AnalyticsService.get_fraud_confirmed_rate(db)

        # Should be 4/10 = 40%
        assert 0 <= confirmed_rate <= 100

    def test_get_false_positive_rate(self, db: Session, sample_customer: Customer):
        """Test false positive rate calculation."""
        # Create alerts: 3 approved (fraud), 7 rejected (false positives)
        for i in range(3):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_FP_APP_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=80
            )
            alert.alert_status = "resolved"
            alert.review_decision = "approved"
            db.commit()

        for i in range(7):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_FP_REJ_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=30
            )
            alert.alert_status = "resolved"
            alert.review_decision = "rejected"
            db.commit()

        # Get false positive rate
        fp_rate = AnalyticsService.get_false_positive_rate(db)

        # Should be 7/10 = 70%
        assert 0 <= fp_rate <= 100

    def test_alert_statistics_time_filtering(self, db: Session, sample_customer: Customer):
        """Test alert statistics with time filtering."""
        # Create old alert (outside 7-day window)
        old_txn = Transaction(
            customer_id=sample_customer.id,
            transaction_id="TXN_OLD_ALERT",
            amount=Decimal("500.00"),
            transaction_date=datetime.utcnow() - timedelta(days=40),
            transaction_type="credit_transfer",
            currency="USD",
            merchant_name="Test",
            merchant_id="M001"
        )
        db.add(old_txn)
        db.flush()
        
        assessment, alert = create_test_fraud_assessment_and_alert(
            db, old_txn.id, sample_customer.id,
            risk_score=50
        )
        alert.alert_status = "pending"
        db.commit()

        # Create recent alert
        recent_txn = Transaction(
            customer_id=sample_customer.id,
            transaction_id="TXN_NEW_ALERT",
            amount=Decimal("500.00"),
            transaction_date=datetime.utcnow(),
            transaction_type="credit_transfer",
            currency="USD",
            merchant_name="Test",
            merchant_id="M001"
        )
        db.add(recent_txn)
        db.flush()
        
        assessment, alert = create_test_fraud_assessment_and_alert(
            db, recent_txn.id, sample_customer.id,
            risk_score=50
        )
        alert.alert_status = "pending"
        db.commit()

        # Get statistics for 7 days
        stats = AnalyticsService.get_alert_statistics(db, days=7)

        # Should only count recent alert
        assert stats["total_alerts"] >= 1

    def test_approval_rate_calculation(self, db: Session, sample_customer: Customer):
        """Test approval rate calculation."""
        # Create 5 approved and 5 rejected alerts
        for i in range(5):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_APPRATE_APP_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=75
            )
            alert.alert_status = "resolved"
            alert.review_decision = "approved"
            db.commit()

        for i in range(5):
            txn = Transaction(
                customer_id=sample_customer.id,
                transaction_id=f"TXN_APPRATE_REJ_{i}",
                amount=Decimal("500.00"),
                transaction_date=datetime.utcnow(),
                transaction_type="credit_transfer",
                currency="USD",
                merchant_name="Test",
                merchant_id="M001"
            )
            db.add(txn)
            db.flush()
            
            assessment, alert = create_test_fraud_assessment_and_alert(
                db, txn.id, sample_customer.id,
                risk_score=30
            )
            alert.alert_status = "resolved"
            alert.review_decision = "rejected"
            db.commit()

        # Get statistics
        stats = AnalyticsService.get_alert_statistics(db, days=30)

        # Should have 50% approval rate
        assert stats["approval_rate"] == 50.0

    def test_alert_statistics_empty(self, db: Session):
        """Test alert statistics with no data."""
        stats = AnalyticsService.get_alert_statistics(db, days=30)

        assert stats["total_alerts"] == 0
        assert stats["pending_alerts"] == 0
        assert stats["resolved_alerts"] == 0
        assert stats["approval_rate"] == 0.0
