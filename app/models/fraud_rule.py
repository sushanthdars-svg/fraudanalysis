"""
Fraud rule model for configurable rule-based detection.
"""

from sqlalchemy import String, DECIMAL, Text, Index, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional, Any, Dict
from app.db.base import BaseModel


class FraudRule(BaseModel):
    """
    Configurable fraud detection rule model.
    Rules are stored in the database for flexible configuration without code changes.
    """
    __tablename__ = "fraud_rules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique rule identifier (e.g., R01, R02)"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Rule configuration
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="high_value, velocity, geographic, duplicate, etc."
    )
    is_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True
    )
    
    # Thresholds and configuration (stored as JSON for flexibility)
    threshold_value: Mapped[Optional[DECIMAL]] = mapped_column(
        DECIMAL(15, 2),
        nullable=True,
        doc="Primary threshold for the rule"
    )
    threshold_unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="amount, count, percentage, hours, minutes, etc."
    )
    threshold_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional configuration parameters as JSON"
    )
    
    # Risk assessment
    severity: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        nullable=False,
        index=True,
        doc="low, medium, high, critical"
    )
    risk_weight: Mapped[DECIMAL] = mapped_column(
        DECIMAL(5, 2),
        default=10,
        nullable=False,
        doc="Weight in risk score calculation (0-100)"
    )
    
    # Conditions and requirements
    required_fields: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Comma-separated list of required fields for rule to apply"
    )
    applicable_transaction_types: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Comma-separated transaction types this rule applies to"
    )
    
    # Rule version and history
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Rule version for tracking changes"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    triggered_rules: Mapped[List["TriggeredRule"]] = relationship(
        "TriggeredRule",
        back_populates="rule"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_rules_rule_id", "rule_id"),
        Index("idx_rules_is_enabled", "is_enabled"),
        Index("idx_rules_rule_type", "rule_type"),
        Index("idx_rules_severity", "severity"),
    )
    
    def __repr__(self) -> str:
        return f"<FraudRule(rule_id={self.rule_id}, name={self.name})>"
