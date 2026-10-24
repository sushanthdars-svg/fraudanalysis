from datetime import datetime, timedelta

from app.models.customer import Customer
from app.models.transaction import Transaction
from scripts.generate_synthetic_data import SyntheticDataGenerator


def test_synthetic_transactions_are_recent_and_insert_with_valid_customers(test_session):
    generated = SyntheticDataGenerator.generate_synthetic_transactions(
        n_transactions=6,
        fraud_rate=0.17,
        n_customers=2,
        days=30,
    )

    assert generated["transaction_id"].is_unique
    assert generated["transaction_date"].min() >= datetime.now() - timedelta(days=31)

    inserted = SyntheticDataGenerator.insert_into_database(generated, test_session)

    assert inserted == 6
    assert test_session.query(Transaction).count() == 6
    assert test_session.query(Customer).count() == len(
        generated["customer_id"].unique()
    )
