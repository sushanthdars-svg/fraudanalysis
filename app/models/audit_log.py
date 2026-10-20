"""
Audit log model for comprehensive action logging and compliance.
"""

from sqlalchemy import String, Text, Index, DateTime, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit trail for all significant system actions.
    Enables compliance, forensics, and accountability.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Actor and action
    actor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        doc="User who performed the action, None for system actions"
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="login, logout, create_transaction, create_rule, etc."
    )
    action_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="authentication, transaction, rule, audit, model, etc."
    )
    
    # Target resource
    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="user, transaction, fraud_rule, model, etc."
    )
    target_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="ID of the affected resource"
    )
    target_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable name/reference of the target"
    )
    
    # Operation outcome
    action_status: Mapped[str] = mapped_column(
        String(50),
        default="success",
        nullable=False,
        index=True,
        doc="success, failure, partial"
    )
    status_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if action failed"
    )
    
    # Request context
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Correlation ID for tracing related actions"
    )
    http_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        doc="GET, POST, PUT, DELETE, etc."
    )
    http_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="API endpoint path"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Source IP address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="HTTP User-Agent header"
    )
    
    # Timestamps
    action_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Safe contextual metadata (no sensitive data)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional safe context (NO passwords, tokens, or PII)"
    )
    
    # Data changes (for update operations)
    changes_before: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Previous values before update (safe fields only)"
    )
    changes_after: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="New values after update (safe fields only)"
    )
    
    # Relationships
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[actor_id]
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_audit_actor_id", "actor_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_action_category", "action_category"),
        Index("idx_audit_target_type", "target_type"),
        Index("idx_audit_target_id", "target_id"),
        Index("idx_audit_timestamp", "action_timestamp"),
        Index("idx_audit_status", "action_status"),
        Index("idx_audit_request_id", "request_id"),
        Index("idx_audit_timestamp_actor", "action_timestamp", "actor_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, target={self.target_type}:{self.target_id})>"
