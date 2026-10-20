"""
Investigation case model for alert-to-case workflow.
Tracks fraud investigation cases created from high-risk alerts.
"""

from sqlalchemy import String, Text, Index, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.db.base import BaseModel


class InvestigationCase(BaseModel):
    """
    Investigation case for fraud alerts.
    Tracks investigation workflow, notes, and final outcome.
    """
    __tablename__ = "investigation_cases"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Case identification
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_alerts.id"),
        nullable=False,
        unique=True,
        index=True
    )
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )
    
    # Case type and status
    case_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="FRAUD_CONFIRMED, SUSPICIOUS, FALSE_POSITIVE, UNDER_INVESTIGATION"
    )
    case_status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
        index=True,
        doc="open, under_investigation, closed, escalated"
    )
    
    # Assignment
    assigned_to: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        doc="Analyst ID"
    )
    
    # Investigation details
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Summary of investigation findings"
    )
    
    findings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Structured findings from investigation"
    )
    
    # Timestamps
    case_created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    case_closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # Case notes/comments
    case_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes about the case"
    )
    
    # Escalation
    escalated: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Whether case was escalated"
    )
    escalation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    escalated_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        doc="Manager/supervisor ID if escalated"
    )
    
    # Relationships
    alert: Mapped["FraudAlert"] = relationship(
        "FraudAlert",
        foreign_keys=[alert_id]
    )
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        foreign_keys=[transaction_id]
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        foreign_keys=[customer_id]
    )
    assigned_analyst: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_to]
    )
    case_notes_records: Mapped[List["CaseNote"]] = relationship(
        "CaseNote",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_cases_alert_id", "alert_id"),
        Index("idx_cases_transaction_id", "transaction_id"),
        Index("idx_cases_customer_id", "customer_id"),
        Index("idx_cases_assigned_to", "assigned_to"),
        Index("idx_cases_status", "case_status"),
        Index("idx_cases_type", "case_type"),
        Index("idx_cases_created_at", "case_created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<InvestigationCase(id={self.id}, alert_id={self.alert_id}, status={self.case_status})>"


class CaseNote(BaseModel):
    """
    Individual note/comment on an investigation case.
    Provides audit trail of investigation progress.
    """
    __tablename__ = "case_notes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    case_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_cases.id"),
        nullable=False,
        index=True
    )
    
    analyst_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    note_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    note_type: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
        doc="general, finding, action, decision"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships
    case: Mapped["InvestigationCase"] = relationship(
        "InvestigationCase",
        back_populates="case_notes_records"
    )
    analyst: Mapped["User"] = relationship(
        "User"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_case_notes_case_id", "case_id"),
        Index("idx_case_notes_analyst_id", "analyst_id"),
        Index("idx_case_notes_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<CaseNote(id={self.id}, case_id={self.case_id})>"
