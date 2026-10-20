"""
Transaction model for financial transactions.
"""

from sqlalchemy import String, DECIMAL, DateTime, Text, Index, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from app.db.base import BaseModel


class Transaction(BaseModel):
    """
    Financial transaction model.
    Contains transaction details, amounts, merchant info, and status.
    Stores monetary values as DECIMAL for precision.
    """
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="External transaction ID for idempotency"
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        doc="Transaction timestamp (UTC)"
    )
    
    # Transaction details
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        index=True,
        doc="Transaction amount in base currency"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="ISO 4217 currency code"
    )
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Transaction type and status
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        default="purchase",
        nullable=False,
        index=True,
        doc="purchase, withdrawal, transfer, etc."
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
        nullable=False,
        index=True,
        doc="completed, failed, pending, declined"
    )
    
    # Payment method
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="card",
        nullable=False,
        index=True,
        doc="card, bank_transfer, wallet, cash, etc."
    )
    
    # Location information
    location_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Device and channel info
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="online, atm, pos, phone, etc."
    )
    
    # Additional context
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="True if this is synthetic/test data"
    )
    
    # Fraud label (only for datasets with known truth)
    fraud_label: Mapped[Optional[bool]] = mapped_column(
        default=None,
        nullable=True,
        doc="True/False if confirmed fraud status known, None if unknown"
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="transactions")
    fraud_assessments: Mapped[List["FraudAssessment"]] = relationship(
        "FraudAssessment",
        back_populates="transaction"
    )
    fraud_alerts: Mapped[List["FraudAlert"]] = relationship(
        "FraudAlert",
        back_populates="transaction"
    )
    triggered_rules: Mapped[List["TriggeredRule"]] = relationship(
        "TriggeredRule",
        back_populates="transaction"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_transactions_transaction_id", "transaction_id"),
        Index("idx_transactions_customer_id", "customer_id"),
        Index("idx_transactions_date", "transaction_date"),
        Index("idx_transactions_amount", "amount"),
        Index("idx_transactions_merchant", "merchant_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_is_synthetic", "is_synthetic"),
        Index("idx_transactions_date_customer", "transaction_date", "customer_id"),
        Index("idx_transactions_date_amount", "transaction_date", "amount"),
    )
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.transaction_id}, amount={self.amount}, customer_id={self.customer_id})>"
