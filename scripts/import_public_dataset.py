"""
Import public fraud detection dataset (Kaggle Credit Card Fraud Detection).
Downloads and imports data into the database for training.
"""

import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.customer import Customer
from app.models.transaction import Transaction
from app.db.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PublicDatasetImporter:
    """Import public fraud detection datasets."""
    
    @staticmethod
    def download_kaggle_dataset():
        """
        Download Kaggle Credit Card Fraud Detection dataset.
        Requires kaggle CLI and credentials (~150MB, 284K transactions).
        
        Installation:
            pip install kaggle
            # Set up API credentials: ~/.kaggle/kaggle.json
        """
        try:
            import kaggle
            
            logger.info("Downloading Kaggle Credit Card Fraud Detection dataset...")
            
            # Create data directory
            data_dir = Path('data/raw')
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Download dataset
            kaggle.api.dataset_download_files(
                'mlg-ulb/creditcardfraud',
                path=str(data_dir),
                unzip=True
            )
            
            csv_path = data_dir / 'creditcard.csv'
            if csv_path.exists():
                logger.info(f"Dataset downloaded successfully: {csv_path}")
                return csv_path
            else:
                logger.error("Dataset file not found after download")
                return None
                
        except ImportError:
            logger.error("kaggle library not installed. Install with: pip install kaggle")
            return None
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            return None
    
    @staticmethod
    def load_kaggle_csv(csv_path):
        """Load and parse Kaggle CSV dataset."""
        try:
            logger.info(f"Loading CSV from {csv_path}...")
            df = pd.read_csv(csv_path)
            
            logger.info(f"Dataset shape: {df.shape}")
            logger.info(f"Fraud rate: {df['Class'].mean():.4f}")
            logger.info(f"Fraud cases: {(df['Class'] == 1).sum()}")
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return None
    
    @staticmethod
    def normalize_kaggle_data(df):
        """
        Transform Kaggle dataset to our schema.
        
        Kaggle dataset:
        - V1-V28: PCA-transformed features
        - Amount: Transaction amount
        - Time: Seconds since first transaction
        - Class: 0=legitimate, 1=fraud
        
        Our schema:
        - transaction_id, customer_id, transaction_date, amount
        - merchant_category, location_country, device_id, fraud_label
        """
        try:
            logger.info("Normalizing Kaggle dataset to our schema...")
            
            # Map to our schema
            normalized_df = pd.DataFrame()
            
            # Create transaction IDs
            normalized_df['transaction_id'] = [f'KAGGLE_{i}' for i in range(len(df))]
            
            # Assign customers (distribute across 5000 customers)
            n_customers = 5000
            normalized_df['customer_id'] = np.random.randint(1, n_customers + 1, len(df))
            
            # Create timestamps (spread over 2 days, simulating continuous transactions)
            base_date = datetime(2023, 1, 1)
            seconds_in_2_days = 2 * 24 * 3600
            time_seconds = df['Time'].values % seconds_in_2_days
            normalized_df['transaction_date'] = [
                base_date + timedelta(seconds=int(t)) for t in time_seconds
            ]
            
            # Amount (already in currency units)
            normalized_df['amount'] = df['Amount'].values
            
            # Assign merchant categories based on amount patterns
            def categorize_merchant(amount):
                if amount < 50:
                    return np.random.choice(['grocery', 'gas_station', 'convenience_store'], p=[0.4, 0.3, 0.3])
                elif amount < 200:
                    return np.random.choice(['restaurant', 'online_retail', 'entertainment'], p=[0.4, 0.4, 0.2])
                else:
                    return np.random.choice(['travel', 'online_retail', 'subscription'], p=[0.3, 0.4, 0.3])
            
            normalized_df['merchant_category'] = df['Amount'].apply(categorize_merchant)
            
            # Transaction type
            normalized_df['transaction_type'] = 'purchase'
            
            # Payment method
            normalized_df['payment_method'] = np.random.choice(
                ['card', 'debit', 'bank_transfer'], 
                len(df),
                p=[0.7, 0.2, 0.1]
            )
            
            # Location (mostly US, some other countries)
            countries = np.random.choice(
                ['US', 'CA', 'GB', 'DE', 'FR', 'ES', 'IT', 'NL'],
                len(df),
                p=[0.7, 0.1, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02]
            )
            normalized_df['location_country'] = countries
            
            cities_by_country = {
                'US': ['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix'],
                'CA': ['Toronto', 'Vancouver', 'Montreal'],
                'GB': ['London', 'Manchester', 'Birmingham'],
                'DE': ['Berlin', 'Munich', 'Hamburg'],
                'FR': ['Paris', 'Lyon', 'Marseille'],
                'ES': ['Madrid', 'Barcelona', 'Valencia'],
                'IT': ['Rome', 'Milan', 'Naples'],
                'NL': ['Amsterdam', 'Rotterdam', 'Utrecht']
            }
            
            normalized_df['location_city'] = [
                np.random.choice(cities_by_country.get(c, ['Unknown']))
                for c in countries
            ]
            
            # Device info (assign consistently to customers)
            # Map customer_id to device_id (3 devices per customer on average)
            def get_device(customer_id):
                np.random.seed(customer_id % 1000)
                return f'device_{customer_id % 2000}'
            
            normalized_df['device_id'] = normalized_df['customer_id'].apply(get_device)
            
            # Channel
            normalized_df['channel'] = np.random.choice(
                ['online', 'physical', 'mobile'],
                len(df),
                p=[0.6, 0.3, 0.1]
            )
            
            # Fraud label
            normalized_df['fraud_label'] = df['Class'].values
            
            # Keep original PCA features for reference
            for col in [c for c in df.columns if c.startswith('V')]:
                normalized_df[col] = df[col].values
            
            logger.info(f"Normalized dataset shape: {normalized_df.shape}")
            logger.info(f"Fraud rate: {normalized_df['fraud_label'].mean():.4f}")
            
            return normalized_df
        
        except Exception as e:
            logger.error(f"Failed to normalize dataset: {e}")
            return None
    
    @staticmethod
    def ensure_customers_exist(df, session):
        """Ensure customer records exist for all customer IDs."""
        try:
            logger.info("Ensuring customer records exist...")
            
            customer_ids = df['customer_id'].unique()
            existing_customers = session.query(Customer).all()
            existing_ids = {c.customer_id for c in existing_customers}
            
            missing_ids = set(customer_ids) - existing_ids
            
            if missing_ids:
                logger.info(f"Creating {len(missing_ids)} missing customer records...")
                
                new_customers = []
                for cid in missing_ids:
                    customer = Customer(
                        customer_id=cid,
                        customer_name=f'Customer_{cid}',
                        email=f'customer_{cid}@example.com',
                        account_created_date=datetime(2022, 1, 1),
                        account_status='active'
                    )
                    new_customers.append(customer)
                
                session.add_all(new_customers)
                session.commit()
                logger.info(f"Created {len(new_customers)} customer records")
            else:
                logger.info("All customer records already exist")
        
        except Exception as e:
            logger.error(f"Error ensuring customers exist: {e}")
            session.rollback()
            raise
    
    @staticmethod
    def insert_into_database(df, session, batch_size=1000):
        """Insert transactions into database."""
        try:
            logger.info(f"Inserting {len(df)} transactions into database...")
            
            # Check for duplicates
            existing_ids = {t.transaction_id for t in session.query(Transaction).all()}
            df_new = df[~df['transaction_id'].isin(existing_ids)].copy()
            
            if len(df_new) == 0:
                logger.info("All transactions already exist in database, skipping insert")
                return 0
            
            logger.info(f"Inserting {len(df_new)} new transactions (skipping {len(df) - len(df_new)} duplicates)")
            
            # Ensure customers exist
            PublicDatasetImporter.ensure_customers_exist(df_new, session)
            
            # Insert in batches
            for i in range(0, len(df_new), batch_size):
                batch = df_new.iloc[i:i+batch_size]
                
                transactions = []
                for _, row in batch.iterrows():
                    transaction = Transaction(
                        transaction_id=row['transaction_id'],
                        customer_id=row['customer_id'],
                        transaction_date=row['transaction_date'],
                        amount=float(row['amount']),
                        merchant_category=row['merchant_category'],
                        transaction_type=row['transaction_type'],
                        payment_method=row['payment_method'],
                        location_country=row['location_country'],
                        location_city=row['location_city'],
                        device_id=row['device_id'],
                        channel=row['channel'],
                        fraud_label=int(row['fraud_label'])
                    )
                    transactions.append(transaction)
                
                session.add_all(transactions)
                session.commit()
                
                progress = min(i + batch_size, len(df_new))
                logger.info(f"  Inserted {progress}/{len(df_new)} transactions")
            
            logger.info(f"Successfully inserted {len(df_new)} transactions")
            return len(df_new)
        
        except Exception as e:
            logger.error(f"Error inserting transactions: {e}")
            session.rollback()
            raise
    
    @staticmethod
    def import_kaggle_dataset():
        """Main pipeline to import Kaggle dataset."""
        session = SessionLocal()
        
        try:
            # Download
            csv_path = PublicDatasetImporter.download_kaggle_dataset()
            if csv_path is None:
                logger.warning("Could not download Kaggle dataset. Provide CSV manually.")
                logger.info("Download from: https://www.kaggle.com/mlg-ulb/creditcardfraud")
                return
            
            # Load
            df = PublicDatasetImporter.load_kaggle_csv(csv_path)
            if df is None:
                return
            
            # Normalize to our schema
            df_normalized = PublicDatasetImporter.normalize_kaggle_data(df)
            if df_normalized is None:
                return
            
            # Insert into database
            inserted = PublicDatasetImporter.insert_into_database(df_normalized, session)
            
            logger.info("="*80)
            logger.info(f"Kaggle dataset import completed: {inserted} transactions inserted")
            logger.info("="*80)
        
        except Exception as e:
            logger.error(f"Import pipeline failed: {e}", exc_info=True)
        
        finally:
            session.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import public fraud detection dataset')
    parser.add_argument('--csv', type=str, help='Path to Kaggle CSV file (if already downloaded)')
    parser.add_argument('--download', action='store_true', default=True, help='Download from Kaggle (default: True)')
    
    args = parser.parse_args()
    
    session = SessionLocal()
    
    try:
        if args.csv:
            logger.info(f"Loading CSV from {args.csv}...")
            df = PublicDatasetImporter.load_kaggle_csv(args.csv)
        else:
            df = PublicDatasetImporter.download_kaggle_dataset()
            if df is None:
                return
            df = PublicDatasetImporter.load_kaggle_csv(df)
        
        if df is None:
            return
        
        df_normalized = PublicDatasetImporter.normalize_kaggle_data(df)
        if df_normalized is None:
            return
        
        inserted = PublicDatasetImporter.insert_into_database(df_normalized, session)
        
        logger.info("="*80)
        logger.info(f"Import completed: {inserted} transactions inserted")
        logger.info("="*80)
    
    finally:
        session.close()


if __name__ == '__main__':
    main()
