"""Isolated browser-test API. Never point this at an application database."""

import os
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from sqlalchemy.engine import make_url

    database_url = os.environ.get("E2E_DATABASE_URL", "")
    if not database_url or make_url(database_url).database != "fraud_detection_e2e":
        raise RuntimeError("E2E_DATABASE_URL must point to the dedicated fraud_detection_e2e database")
    os.environ["DATABASE_URL"] = database_url
    os.environ["SECRET_KEY"] = uuid4().hex + uuid4().hex
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "false"

    import numpy as np
    import uvicorn
    from app.main import app
    from app.api import models
    from app.core.security import hash_password
    from app.db.base import Base
    from app.db.database import get_engine, get_db_session
    from app.ml.train import ModelTrainer
    from app.ml.predict import ModelPredictor
    from app.models import Customer, FraudAssessment, FraudAlert, FraudRule, Transaction, User
    from scripts.generate_synthetic_data import SyntheticDataGenerator

    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    random.seed(42)
    np.random.seed(42)
    with get_db_session() as db:
        for role in ("admin", "analyst", "viewer"):
            db.add(User(
                email=f"{role}@example.com", full_name=f"Test {role.title()}",
                password_hash=hash_password("Browser-Test-Only-2026"), role=role, is_active=True,
            ))
        for customer_id in range(1, 31):
            db.add(Customer(id=customer_id, customer_id=f"E2E-{customer_id}", name=f"Test customer {customer_id}"))
        db.add(FraudRule(
            rule_id="E2E-HIGH-VALUE", name="High value payment", description="Review large payments",
            rule_type="high_value", severity="high", risk_weight=30, threshold_value=1000,
        ))
        db.flush()
        data = SyntheticDataGenerator.generate_synthetic_transactions(
            n_transactions=1000, n_customers=30, fraud_rate=0.15,
        )
        for index, row in data.iterrows():
            transaction = Transaction(
                transaction_id=f"E2E-{index:05d}", customer_id=int(row["customer_id"]),
                transaction_date=row["transaction_date"], amount=float(row["amount"]),
                merchant_name=row["merchant_name"], merchant_category=row["merchant_category"],
                payment_method=row["payment_method"], transaction_type="purchase",
                channel=row["channel"], device_id=row["device_id"],
                location_country=row["location_country"], location_city=row["location_city"],
                fraud_label=bool(row["fraud_label"]), is_synthetic=True,
            )
            db.add(transaction)
            if index < 60:
                db.flush()
                assessment = FraudAssessment(
                    transaction_id=transaction.id,
                    risk_score=80 if index < 3 else 20,
                    risk_category="high" if index < 3 else "low",
                    rules_triggered_count=1 if index < 3 else 0,
                )
                db.add(assessment)
                db.flush()
                if index < 3:
                    db.add(FraudAlert(
                        transaction_id=transaction.id, customer_id=transaction.customer_id,
                        assessment_id=assessment.id, alert_severity="high", alert_status="PENDING",
                        alert_reason="Browser test review queue", triggered_rules_summary="High value payment",
                    ))
        db.commit()

    with TemporaryDirectory(prefix="foresight-e2e-") as directory:
        models.MODELS_DIR = ModelTrainer.MODELS_DIR = ModelPredictor.MODELS_DIR = Path(directory)
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")


if __name__ == "__main__":
    main()
