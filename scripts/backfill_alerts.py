"""Create review-queue alerts for scored transactions that do not have one yet."""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import get_session_factory
from app.models import FraudAlert, FraudAssessment, Transaction

logger = logging.getLogger(__name__)


def severity_for(score: float) -> str:
    if score >= 71:
        return "high"
    if score >= 31:
        return "medium"
    return "low"


def backfill(batch_size: int = 500) -> int:
    session = get_session_factory()()
    created = 0
    try:
        rows = (
            session.query(FraudAssessment, Transaction)
            .join(Transaction, Transaction.id == FraudAssessment.transaction_id)
            .outerjoin(FraudAlert, FraudAlert.transaction_id == Transaction.id)
            .filter(FraudAlert.id.is_(None))
            .filter(FraudAssessment.risk_category.in_(("medium", "high")))
            .all()
        )
        for assessment, transaction in rows:
            score = float(assessment.risk_score)
            session.add(
                FraudAlert(
                    transaction_id=transaction.id,
                    customer_id=transaction.customer_id,
                    assessment_id=assessment.id,
                    alert_severity=severity_for(score),
                    alert_status="pending",
                    alert_reason=(
                        f"Risk score {score:.1f} ({assessment.risk_category}) for "
                        f"{transaction.amount} {transaction.currency} at "
                        f"{transaction.merchant_name or 'unknown merchant'}"
                    ),
                    triggered_rules_summary=(
                        f"{assessment.rules_triggered_count} detection rule(s) triggered"
                    ),
                    alert_created_at=transaction.transaction_date or datetime.utcnow(),
                )
            )
            created += 1
            if created % batch_size == 0:
                session.commit()
        session.commit()
        logger.info("Created %s alerts", created)
        return created
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    backfill()
