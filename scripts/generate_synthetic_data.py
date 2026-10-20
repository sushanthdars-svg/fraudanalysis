"""
Generate synthetic transaction data for model training.
Creates realistic fraud and legitimate transaction patterns.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session
import logging
import random

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generates synthetic transaction data for training."""
    
    MERCHANT_CATEGORIES = [
        'grocery', 'restaurant', 'gas_station', 'online_retail', 'entertainment',
        'travel', 'utilities', 'healthcare', 'insurance', 'other'
    ]
    
    COUNTRIES = ['US', 'CA', 'UK', 'DE', 'FR']
    CHANNELS = ['online', 'atm', 'pos', 'phone']
    PAYMENT_METHODS = ['card', 'bank_transfer', 'wallet', 'cash']
    
    @staticmethod
    def generate_legitimate_transaction(
        customer_id: int,
        base_time: datetime,
        customer_profile: dict
    ) -> dict:
        """Generate a realistic legitimate transaction."""
        
        # Amount based on category
        category = random.choice(SyntheticDataGenerator.MERCHANT_CATEGORIES)
        if category == 'grocery':
            amount = np.random.normal(75, 30)
        elif category == 'restaurant':
            amount = np.random.normal(50, 25)
        elif category == 'gas_station':
            amount = np.random.normal(60, 15)
        elif category == 'online_retail':
            amount = np.random.normal(100, 60)
        elif category == 'travel':
            amount = np.random.normal(300, 200)
        else:
            amount = np.random.normal(100, 50)
        
        amount = max(1, amount)
        
        # Realistic timing
        hour = random.gauss(12, 8)  # Peak around noon
        hour = max(0, min(23, hour))
        
        transaction_time = base_time.replace(hour=int(hour), minute=random.randint(0, 59))
        
        return {
            'customer_id': customer_id,
            'transaction_date': transaction_time,
            'amount': round(amount, 2),
            'merchant_category': category,
            'transaction_type': 'purchase',
            'payment_method': random.choice(SyntheticDataGenerator.PAYMENT_METHODS),
            'location_country': customer_profile.get('home_country', 'US'),
            'location_city': customer_profile.get('home_city', 'New York'),
            'channel': random.choice(SyntheticDataGenerator.CHANNELS),
            'device_id': random.choice(customer_profile.get('known_devices', ['device_1'])),
            'fraud_label': False,
        }
    
    @staticmethod
    def generate_fraud_transaction(
        customer_id: int,
        base_time: datetime,
        customer_profile: dict
    ) -> dict:
        """Generate a fraudulent transaction with suspicious patterns."""
        
        fraud_type = random.choice(['high_amount', 'unusual_location', 'unusual_time', 'unusual_merchant'])
        
        if fraud_type == 'high_amount':
            # Unusually high amount
            category = random.choice(['online_retail', 'travel', 'entertainment'])
            amount = np.random.normal(5000, 1000)
        elif fraud_type == 'unusual_location':
            # Transaction from unusual location
            category = random.choice(SyntheticDataGenerator.MERCHANT_CATEGORIES)
            amount = np.random.normal(200, 100)
        elif fraud_type == 'unusual_time':
            # Transaction at unusual hour
            category = random.choice(SyntheticDataGenerator.MERCHANT_CATEGORIES)
            amount = np.random.normal(150, 80)
        else:  # unusual_merchant
            # Suspicious merchant category
            category = 'online_retail'
            amount = np.random.normal(500, 300)
        
        amount = max(1, amount)
        
        # Suspicious timing
        if fraud_type == 'unusual_time':
            hour = random.choice([2, 3, 4, 5])  # Night hours
        else:
            hour = random.randint(0, 23)
        
        transaction_time = base_time.replace(hour=hour, minute=random.randint(0, 59))
        
        # Possibly different location
        if fraud_type == 'unusual_location':
            country = random.choice([c for c in SyntheticDataGenerator.COUNTRIES 
                                   if c != customer_profile.get('home_country', 'US')])
        else:
            country = customer_profile.get('home_country', 'US')
        
        # Possibly new device
        if random.random() < 0.3:
            device_id = f"device_fraud_{random.randint(1, 1000)}"
        else:
            device_id = random.choice(customer_profile.get('known_devices', ['device_1']))
        
        return {
            'customer_id': customer_id,
            'transaction_date': transaction_time,
            'amount': round(amount, 2),
            'merchant_category': category,
            'transaction_type': 'purchase',
            'payment_method': random.choice(SyntheticDataGenerator.PAYMENT_METHODS),
            'location_country': country,
            'location_city': 'Unknown City',
            'channel': random.choice(SyntheticDataGenerator.CHANNELS),
            'device_id': device_id,
            'fraud_label': True,
        }
    
    @staticmethod
    def generate_synthetic_transactions(
        n_transactions: int = 50000,
        fraud_rate: float = 0.07,
        n_customers: int = 1000
    ) -> pd.DataFrame:
        """
        Generate synthetic transaction dataset.
        
        Args:
            n_transactions: Total number of transactions to generate
            fraud_rate: Fraction of fraudulent transactions (0.07 = 7%)
            n_customers: Number of unique customers
        
        Returns:
            DataFrame with synthetic transactions
        """
        logger.info(f"Generating {n_transactions} synthetic transactions ({fraud_rate*100:.1f}% fraud rate)...")
        
        # Generate customer profiles
        customer_profiles = {}
        for cid in range(1, n_customers + 1):
            customer_profiles[cid] = {
                'home_country': random.choice(SyntheticDataGenerator.COUNTRIES),
                'home_city': f"City_{cid % 50}",
                'known_devices': [f'device_{cid}_1', f'device_{cid}_2'],
            }
        
        transactions = []
        base_date = datetime(2023, 1, 1)
        
        n_fraud = int(n_transactions * fraud_rate)
        n_legitimate = n_transactions - n_fraud
        
        # Generate legitimate transactions
        for i in range(n_legitimate):
            if i % 5000 == 0:
                logger.info(f"Generated {i} legitimate transactions...")
            
            customer_id = random.randint(1, n_customers)
            days_offset = random.randint(0, 365)
            transaction_time = base_date + timedelta(days=days_offset)
            
            transaction = SyntheticDataGenerator.generate_legitimate_transaction(
                customer_id, transaction_time, customer_profiles[customer_id]
            )
            transaction['transaction_id'] = f"TXN_LEGIT_{i:08d}"
            transaction['merchant_name'] = f"Merchant_{random.randint(1, 5000)}"
            transaction['merchant_id'] = f"M{random.randint(10000, 99999)}"
            transaction['is_synthetic'] = True
            
            transactions.append(transaction)
        
        # Generate fraudulent transactions
        for i in range(n_fraud):
            if i % 1000 == 0:
                logger.info(f"Generated {i} fraudulent transactions...")
            
            customer_id = random.randint(1, n_customers)
            days_offset = random.randint(0, 365)
            transaction_time = base_date + timedelta(days=days_offset)
            
            transaction = SyntheticDataGenerator.generate_fraud_transaction(
                customer_id, transaction_time, customer_profiles[customer_id]
            )
            transaction['transaction_id'] = f"TXN_FRAUD_{i:08d}"
            transaction['merchant_name'] = f"Suspicious_Merchant_{random.randint(1, 5000)}"
            transaction['merchant_id'] = f"M_FRAUD{random.randint(10000, 99999)}"
            transaction['is_synthetic'] = True
            
            transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        df = df.sample(frac=1).reset_index(drop=True)  # Shuffle
        
        logger.info(f"Generated {len(df)} synthetic transactions")
        logger.info(f"Fraud distribution: {df['fraud_label'].mean():.2%}")
        
        return df
    
    @staticmethod
    def insert_into_database(
        df: pd.DataFrame,
        session: Session,
        batch_size: int = 1000
    ) -> int:
        """
        Insert synthetic transactions into database.
        
        Args:
            df: DataFrame with transactions
            session: Database session
            batch_size: Number of transactions per batch insert
        
        Returns:
            Number of transactions inserted
        """
        from app.models import Transaction, Customer
        
        logger.info(f"Inserting {len(df)} transactions into database...")
        
        # Ensure all customers exist
        unique_customers = df['customer_id'].unique()
        for cid in unique_customers:
            customer = session.query(Customer).filter(Customer.id == cid).first()
            if not customer:
                customer = Customer(
                    id=cid,
                    name=f"Customer_{cid}",
                    email=f"customer_{cid}@example.com",
                    phone=f"+1-555-{random.randint(1000, 9999):04d}",
                    status='active'
                )
                session.add(customer)
        
        session.commit()
        
        # Insert transactions in batches
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                transaction = Transaction(
                    transaction_id=row['transaction_id'],
                    customer_id=int(row['customer_id']),
                    transaction_date=row['transaction_date'],
                    amount=row['amount'],
                    currency='USD',
                    merchant_name=row.get('merchant_name', 'Unknown'),
                    merchant_id=row.get('merchant_id'),
                    merchant_category=row['merchant_category'],
                    transaction_type=row['transaction_type'],
                    status='completed',
                    payment_method=row['payment_method'],
                    location_country=row['location_country'],
                    location_city=row['location_city'],
                    device_id=row.get('device_id'),
                    channel=row['channel'],
                    is_synthetic=row.get('is_synthetic', True),
                    fraud_label=bool(row['fraud_label']),
                )
                session.add(transaction)
            
            session.commit()
            logger.info(f"Inserted {min(i + batch_size, len(df))}/{len(df)} transactions")
        
        logger.info(f"Successfully inserted {len(df)} transactions")
        return len(df)


def main():
    """Generate and insert synthetic data."""
    from app.db.database import SessionLocal
    
    session = SessionLocal()
    
    try:
        # Generate synthetic data
        df = SyntheticDataGenerator.generate_synthetic_transactions(
            n_transactions=50000,
            fraud_rate=0.07,
            n_customers=1000
        )
        
        # Insert into database
        inserted = SyntheticDataGenerator.insert_into_database(df, session)
        
        logger.info(f"Synthetic data generation complete. {inserted} transactions inserted.")
    
    finally:
        session.close()


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(__file__).rsplit('\\', 3)[0])
    
    logging.basicConfig(level=logging.INFO)
    main()
