"""
Customer model for transaction party information.
"""

from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from app.db.base import BaseModel


class Customer(BaseModel):
    """
    Customer/account holder model.
    Contains customer demographic and historical behavior information.
    """
    __tablename__ = "customers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="External customer ID from source system"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customer_type: Mapped[str] = mapped_column(
        String(50),
        default="individual",
        nullable=False,
        doc="individual, business, etc."
    )
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    risk_profile: Mapped[str] = mapped_column(
        String(50),
        default="low",
        nullable=False,
        doc="low, medium, high"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="customer"
    )
    fraud_alerts: Mapped[List["FraudAlert"]] = relationship(
        "FraudAlert",
        back_populates="customer"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_customers_customer_id", "customer_id"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_risk_profile", "risk_profile"),
        Index("idx_customers_is_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Customer(customer_id={self.customer_id}, name={self.name})>"
