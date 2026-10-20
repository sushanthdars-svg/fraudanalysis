"""
Fraud alert and assessment models for detection results.
"""

from sqlalchemy import String, DECIMAL, Text, Index, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.db.base import BaseModel


class FraudAssessment(BaseModel):
    """
    Risk assessment and fraud detection results for a transaction.
    Stores rule-based and ML detection outputs, risk score, and explanations.
    """
    __tablename__ = "fraud_assessments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Risk score and category
    risk_score: Mapped[DECIMAL] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        doc="Final risk score (0-100)"
    )
    risk_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="low, medium, high"
    )
    
    # Rule-based detection
    rules_triggered_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # ML detection
    ml_score: Mapped[Optional[DECIMAL]] = mapped_column(
        DECIMAL(5, 4),
        nullable=True,
        doc="ML model fraud probability (0-1)"
    )
    ml_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Version of ML model used"
    )
    
    # Assessment metadata
    engine_version: Mapped[str] = mapped_column(
        String(50),
        default="1.0",
        nullable=False
    )
    assessment_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Explanation and metadata
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable explanation of risk assessment"
    )
    assessment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional assessment context as JSON"
    )
    
    # Data quality indicators
    missing_features: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Comma-separated list of missing features affecting assessment"
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="fraud_assessments"
    )
    triggered_rules: Mapped[List["TriggeredRule"]] = relationship(
        "TriggeredRule",
        back_populates="assessment"
    )
    fraud_alerts: Mapped[List["FraudAlert"]] = relationship(
        "FraudAlert",
        back_populates="assessment"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_assessments_transaction_id", "transaction_id"),
        Index("idx_assessments_risk_category", "risk_category"),
        Index("idx_assessments_timestamp", "assessment_timestamp"),
        Index("idx_assessments_ml_score", "ml_score"),
    )
    
    def __repr__(self) -> str:
        return f"<FraudAssessment(transaction_id={self.transaction_id}, risk_score={self.risk_score})>"


class TriggeredRule(BaseModel):
    """
    Record of a fraud rule being triggered for a transaction.
    Links transactions to the rules that flagged them.
    """
    __tablename__ = "triggered_rules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_assessments.id"),
        nullable=False,
        index=True
    )
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        index=True
    )
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_rules.id"),
        nullable=False,
        index=True
    )
    
    # Rule trigger details
    trigger_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    rule_explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable explanation of why rule triggered"
    )
    triggered_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Values that caused rule trigger"
    )
    
    # Relationships
    assessment: Mapped["FraudAssessment"] = relationship(
        "FraudAssessment",
        back_populates="triggered_rules"
    )
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="triggered_rules"
    )
    rule: Mapped["FraudRule"] = relationship(
        "FraudRule",
        back_populates="triggered_rules"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_triggered_assessment_id", "assessment_id"),
        Index("idx_triggered_transaction_id", "transaction_id"),
        Index("idx_triggered_rule_id", "rule_id"),
    )
    
    def __repr__(self) -> str:
        return f"<TriggeredRule(transaction_id={self.transaction_id}, rule_id={self.rule_id})>"


class FraudAlert(BaseModel):
    """
    High-risk alert created for transactions requiring analyst review.
    Contains alert status, review notes, and audit trail.
    """
    __tablename__ = "fraud_alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_assessments.id"),
        nullable=False,
        index=True
    )
    
    # Alert severity and status
    alert_severity: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        nullable=False,
        index=True,
        doc="low, medium, high, critical"
    )
    alert_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
        doc="pending, under_review, resolved, dismissed"
    )
    
    # Alert details
    alert_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Summary of why alert was created"
    )
    triggered_rules_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Summary of triggered rules"
    )
    
    # Analyst review
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    review_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    review_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="approved, rejected, escalated, etc."
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Alert timestamps
    alert_created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    alert_resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="fraud_alerts"
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="fraud_alerts"
    )
    assessment: Mapped["FraudAssessment"] = relationship(
        "FraudAssessment",
        back_populates="fraud_alerts"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_alerts_transaction_id", "transaction_id"),
        Index("idx_alerts_customer_id", "customer_id"),
        Index("idx_alerts_status", "alert_status"),
        Index("idx_alerts_severity", "alert_severity"),
        Index("idx_alerts_created_at", "alert_created_at"),
        Index("idx_alerts_status_created", "alert_status", "alert_created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<FraudAlert(id={self.id}, status={self.alert_status})>"
