"""
Transaction service for handling transaction operations.
Includes duplicate detection, validation, and batch import logic.
"""

import csv
import logging
from io import StringIO
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.fraud_alert import FraudAssessment
from app.schemas import TransactionCreate
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction operations."""
    
    @staticmethod
    def create_transaction(
        db: Session,
        transaction_create: TransactionCreate,
        audit_user_id: Optional[int] = None
    ) -> Transaction:
        """
        Create a new transaction with validation.
        
        Args:
            db: Database session
            transaction_create: Transaction creation schema
            audit_user_id: User ID for audit logging
            
        Returns:
            Created Transaction object
            
        Raises:
            ValueError: If transaction validation fails
            IntegrityError: If transaction_id already exists
        """
        # Verify customer exists
        customer = db.query(Customer).filter(
            Customer.id == transaction_create.customer_id
        ).first()
        if not customer:
            raise ValueError(f"Customer with ID {transaction_create.customer_id} not found")
        
        # Verify transaction_id is unique
        existing = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_create.transaction_id
        ).first()
        if existing:
            raise ValueError(f"Transaction with ID {transaction_create.transaction_id} already exists")
        
        # Create transaction
        transaction = Transaction(
            **transaction_create.model_dump()
        )
        
        db.add(transaction)
        try:
            db.commit()
            db.refresh(transaction)
            
            # Audit log
            AuditService.log_transaction_creation(
                db=db,
                actor_id=audit_user_id,
                transaction_id=transaction.transaction_id,
                amount=transaction.amount,
                customer_id=str(transaction.customer_id)
            )
            
            logger.info(f"Transaction created: {transaction.transaction_id}")
            return transaction
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Transaction creation failed: {e}")
            raise ValueError("Transaction creation failed due to database constraint")
    
    @staticmethod
    def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            db: Database session
            transaction_id: Transaction primary key
            
        Returns:
            Transaction object or None
        """
        return db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
    
    @staticmethod
    def list_transactions(
        db: Session,
        page: int = 1,
        limit: int = 50,
        customer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        merchant_id: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> tuple[List[Transaction], int]:
        """
        List transactions with filtering and pagination.
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            limit: Results per page
            customer_id: Filter by customer
            start_date: Filter by start date
            end_date: Filter by end date
            min_amount: Filter by minimum amount
            max_amount: Filter by maximum amount
            merchant_id: Filter by merchant
            status: Filter by transaction status
            
        Returns:
            Tuple of (transactions list, total count)
        """
        query = db.query(Transaction)
        
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        if merchant_id:
            query = query.filter(Transaction.merchant_id == merchant_id)
        if transaction_id:
            query = query.filter(
                Transaction.transaction_id.ilike(f"%{transaction_id}%")
            )
        if status:
            query = query.filter(Transaction.status == status)
        if risk_level:
            query = query.join(
                FraudAssessment,
                FraudAssessment.transaction_id == Transaction.id,
            ).filter(
                func.lower(FraudAssessment.risk_category) == risk_level.lower()
            )
        
        total_count = query.count()
        
        # Order by transaction date descending
        transactions = query.order_by(
            desc(Transaction.transaction_date)
        ).offset((page - 1) * limit).limit(limit).all()
        
        return transactions, total_count
    
    @staticmethod
    def detect_duplicate(
        db: Session,
        customer_id: int,
        amount: Decimal,
        merchant_id: Optional[str],
        time_window_minutes: int = 5
    ) -> Optional[Transaction]:
        """
        Detect duplicate transaction within time window.
        Same customer, amount, and merchant within N minutes.
        
        Args:
            db: Database session
            customer_id: Customer ID
            amount: Transaction amount
            merchant_id: Merchant ID
            time_window_minutes: Time window for duplicate detection
            
        Returns:
            Transaction if duplicate found, None otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        duplicate = db.query(Transaction).filter(
            and_(
                Transaction.customer_id == customer_id,
                Transaction.amount == amount,
                Transaction.merchant_id == merchant_id,
                Transaction.transaction_date >= cutoff_time,
                Transaction.status == "completed"
            )
        ).order_by(desc(Transaction.transaction_date)).first()
        
        return duplicate
    
    @staticmethod
    def bulk_import(
        db: Session,
        file_content: str,
        idempotency_key: str,
        audit_user_id: Optional[int] = None,
        max_rows: int = 100000
    ) -> Dict[str, Any]:
        """
        Bulk import transactions from CSV content.
        
        Args:
            db: Database session
            file_content: CSV file content as string
            idempotency_key: Unique key for idempotency
            audit_user_id: User ID for audit logging
            max_rows: Maximum number of rows to import
            
        Returns:
            Import result with success/failure counts and details
            
        Raises:
            ValueError: If CSV format is invalid
        """
        result = {
            "idempotency_key": idempotency_key,
            "total_rows": 0,
            "successful": 0,
            "failed": 0,
            "duplicates_skipped": 0,
            "errors": [],
            "failed_rows": []
        }
        
        try:
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(file_content))
            
            if not csv_reader.fieldnames:
                raise ValueError("CSV file is empty")
            
            # Validate required headers
            required_headers = {
                "transaction_id", "customer_id", "transaction_date",
                "amount", "merchant_id"
            }
            if not required_headers.issubset(set(csv_reader.fieldnames)):
                missing = required_headers - set(csv_reader.fieldnames)
                raise ValueError(f"Missing required CSV headers: {missing}")
            
            # Process rows
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is 1)
                if row_num > max_rows + 1:
                    result["errors"].append(f"Import limited to {max_rows} rows")
                    break
                
                result["total_rows"] += 1
                
                try:
                    # Parse and validate row data
                    transaction_id = row.get("transaction_id", "").strip()
                    customer_id_str = row.get("customer_id", "").strip()
                    transaction_date_str = row.get("transaction_date", "").strip()
                    amount_str = row.get("amount", "").strip()
                    merchant_id = row.get("merchant_id", "").strip() or None
                    merchant_name = row.get("merchant_name", "").strip() or None
                    transaction_type = row.get("transaction_type", "purchase").strip() or "purchase"
                    payment_method = row.get("payment_method", "card").strip() or "card"
                    location_country = row.get("location_country", "").strip() or None
                    location_city = row.get("location_city", "").strip() or None
                    
                    # Validation
                    if not transaction_id:
                        raise ValueError("transaction_id is required")
                    if not customer_id_str:
                        raise ValueError("customer_id is required")
                    if not transaction_date_str:
                        raise ValueError("transaction_date is required")
                    if not amount_str:
                        raise ValueError("amount is required")
                    
                    # Check if transaction already exists
                    existing = db.query(Transaction).filter(
                        Transaction.transaction_id == transaction_id
                    ).first()
                    if existing:
                        result["duplicates_skipped"] += 1
                        continue
                    
                    # Convert types
                    try:
                        customer_id = int(customer_id_str)
                    except ValueError:
                        raise ValueError(f"Invalid customer_id: {customer_id_str}")
                    
                    try:
                        amount = Decimal(amount_str)
                    except:
                        raise ValueError(f"Invalid amount: {amount_str}")
                    
                    try:
                        transaction_date = datetime.fromisoformat(
                            transaction_date_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        raise ValueError(f"Invalid transaction_date format: {transaction_date_str}")
                    
                    # Verify customer exists
                    customer = db.query(Customer).filter(
                        Customer.id == customer_id
                    ).first()
                    if not customer:
                        raise ValueError(f"Customer with ID {customer_id} not found")
                    
                    # Create transaction
                    transaction = Transaction(
                        transaction_id=transaction_id,
                        customer_id=customer_id,
                        transaction_date=transaction_date,
                        amount=amount,
                        merchant_id=merchant_id,
                        merchant_name=merchant_name,
                        transaction_type=transaction_type,
                        payment_method=payment_method,
                        location_country=location_country,
                        location_city=location_city,
                        status="completed",
                        is_synthetic=False
                    )
                    
                    db.add(transaction)
                    result["successful"] += 1
                
                except Exception as e:
                    result["failed"] += 1
                    error_msg = str(e)
                    result["failed_rows"].append({
                        "row_number": row_num,
                        "transaction_id": row.get("transaction_id", ""),
                        "error": error_msg
                    })
                    logger.warning(f"Row {row_num} import failed: {error_msg}")
            
            # Commit all successful transactions
            if result["successful"] > 0:
                try:
                    db.commit()
                    AuditService.log_batch_import(
                        db=db,
                        actor_id=audit_user_id,
                        row_count=result["successful"],
                        idempotency_key=idempotency_key
                    )
                except Exception as e:
                    db.rollback()
                    result["successful"] = 0
                    result["failed"] = result["total_rows"]
                    result["errors"].append(f"Database commit failed: {str(e)}")
                    logger.error(f"Batch import commit failed: {e}")
            
            logger.info(
                f"Batch import completed: {result['successful']} successful, "
                f"{result['failed']} failed, {result['duplicates_skipped']} duplicates"
            )
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Batch import failed: {e}")
            raise ValueError(f"CSV import failed: {str(e)}")
        
        return result
