"""
Pytest configuration for test database setup.
Uses in-memory SQLite database for all tests.
"""

import pytest
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime

from app.db.base import Base
from app.db.database import get_db


# Create test engine with in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


def create_test_engine():
    """Create test database engine using in-memory SQLite."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine using in-memory SQLite."""
    engine = create_test_engine()
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session with fresh transaction for each test."""
    from sqlalchemy import text
    
    # Clear all data before each test
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Delete data from all tables to ensure isolation between tests
    connection.execute(text("PRAGMA foreign_keys=OFF"))
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(text(f"DELETE FROM {table.name}"))
    connection.execute(text("PRAGMA foreign_keys=ON"))
    
    transaction.commit()
    connection.close()
    
    session = sessionmaker(bind=test_engine, expire_on_commit=False)()
    
    yield session
    
    # Rollback any uncommitted changes
    session.rollback()
    session.close()


@pytest.fixture
def test_client(test_engine, test_session):
    """Create FastAPI test client with test database override."""
    # Set the test engine on the database module
    import app.db.database as db_module
    db_module.set_engine(test_engine)
    
    def override_get_db():
        try:
            yield test_session
        finally:
            pass  # Don't close in override
    
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup routers (already done at app creation)
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    db_module.set_engine(None)  # Reset


@pytest.fixture
def auth_headers(test_session, test_client):
    """Create auth headers for authenticated API requests."""
    from jose import jwt
    from app.core.config import get_settings
    from datetime import datetime, timedelta, timezone
    from app.models.user import User
    from app.core.permissions import UserRole
    from app.core.security import hash_password
    
    settings = get_settings()
    
    # Create an admin user for auth
    user = User(
        email="test_admin@example.com",
        password_hash=hash_password("test123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return {"Authorization": f"Bearer {token}"}


# Helper function for creating test data
def create_test_transaction(
    session: Session,
    customer_id: int,
    amount: float = 1000.0,
    transaction_date: datetime = None,
    transaction_type: str = "purchase",
    status: str = "completed",
    merchant_name: str = "Test Merchant",
    merchant_id: str = "M001",
    currency: str = "USD"
):
    """Helper to create a transaction with required fields."""
    from app.models.transaction import Transaction
    from decimal import Decimal
    
    if transaction_date is None:
        transaction_date = datetime.utcnow()
    
    txn = Transaction(
        transaction_id=f"TXN_{customer_id}_{int(datetime.utcnow().timestamp() * 1000)}",
        customer_id=customer_id,
        amount=Decimal(str(amount)),
        transaction_date=transaction_date,
        transaction_type=transaction_type,
        status=status,
        merchant_name=merchant_name,
        merchant_id=merchant_id,
        currency=currency
    )
    session.add(txn)
    session.flush()  # Ensure ID is assigned
    return txn


def create_test_fraud_assessment_and_alert(
    session: Session,
    transaction_id: int,
    customer_id: int,
    risk_score: float = 50.0,
    risk_category: str = "medium",
    alert_severity: str = "medium",
    alert_status: str = "pending",
    alert_reason: str = "Fraud assessment alert"
):
    """Helper to create FraudAssessment and associated FraudAlert."""
    from app.models.fraud_alert import FraudAssessment, FraudAlert
    from decimal import Decimal
    
    # Create FraudAssessment with risk_score
    assessment = FraudAssessment(
        transaction_id=transaction_id,
        risk_score=Decimal(str(risk_score)),
        risk_category=risk_category,
        rules_triggered_count=0,
        engine_version="1.0"
    )
    session.add(assessment)
    session.flush()  # Ensure ID is assigned
    
    # Create FraudAlert linked to assessment
    alert = FraudAlert(
        transaction_id=transaction_id,
        customer_id=customer_id,
        assessment_id=assessment.id,
        alert_severity=alert_severity,
        alert_status=alert_status,
        alert_reason=alert_reason
    )
    session.add(alert)
    session.flush()
    
    return assessment, alert
