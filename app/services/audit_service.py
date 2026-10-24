"""
Audit logging service for compliance and forensics.
Records all significant system actions with context.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.models import AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging operations."""
    
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        action_category: str,
        target_type: str,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        actor_id: Optional[int] = None,
        status: str = "success",
        status_message: Optional[str] = None,
        http_method: Optional[str] = None,
        http_path: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        changes_before: Optional[Dict[str, Any]] = None,
        changes_after: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            action: Action performed (login, create_transaction, etc.)
            action_category: Category of action (authentication, transaction, rule, etc.)
            target_type: Type of resource affected (user, transaction, etc.)
            target_id: ID of the affected resource
            target_name: Human-readable name of the affected resource
            actor_id: ID of the user who performed the action (None for system)
            status: Action status (success, failure, partial)
            status_message: Error message if action failed
            http_method: HTTP method of the request
            http_path: HTTP path of the request
            ip_address: IP address of the requester
            request_id: Correlation ID for request tracing
            metadata: Safe contextual metadata (NO passwords, tokens, PII)
            changes_before: Previous values before update (safe fields only)
            changes_after: New values after update (safe fields only)
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            action_category=action_category,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            action_status=status,
            status_message=status_message,
            http_method=http_method,
            http_path=http_path,
            ip_address=ip_address,
            request_id=request_id,
            action_timestamp=datetime.now(timezone.utc),
            metadata=metadata,
            changes_before=changes_before,
            changes_after=changes_after,
        )
        
        try:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            logger.debug(f"Audit log created: {action} on {target_type}:{target_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit failures shouldn't block operations
        
        return audit_log
    
    @staticmethod
    def log_login(
        db: Session,
        actor_id: Optional[int],
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log a login attempt."""
        return AuditService.log_action(
            db=db,
            action="login",
            action_category="authentication",
            target_type="user",
            target_id=str(actor_id) if actor_id else email,
            target_name=email,
            actor_id=actor_id,
            status="success" if success else "failure",
            status_message="Login successful" if success else "Invalid credentials",
            ip_address=ip_address,
            metadata={"email": email}
        )
    
    @staticmethod
    def log_transaction_creation(
        db: Session,
        actor_id: Optional[int],
        transaction_id: str,
        customer_id: int,
        amount: float,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log transaction creation."""
        return AuditService.log_action(
            db=db,
            action="create_transaction",
            action_category="transaction",
            target_type="transaction",
            target_id=transaction_id,
            target_name=f"Transaction {transaction_id}",
            actor_id=actor_id,
            ip_address=ip_address,
            metadata={"customer_id": customer_id, "amount": amount}
        )
    
    @staticmethod
    def log_fraud_assessment(
        db: Session,
        actor_id: Optional[int],
        transaction_id: int,
        risk_score: float,
        risk_category: str,
    ) -> AuditLog:
        """Log fraud assessment."""
        return AuditService.log_action(
            db=db,
            action="assess_transaction",
            action_category="fraud_detection",
            target_type="fraud_assessment",
            target_id=str(transaction_id),
            target_name=f"Assessment for transaction {transaction_id}",
            actor_id=actor_id,
            metadata={"risk_score": risk_score, "risk_category": risk_category}
        )
    
    @staticmethod
    def log_alert_review(
        db: Session,
        actor_id: int,
        alert_id: int,
        decision: str,
        notes: Optional[str] = None,
    ) -> AuditLog:
        """Log fraud alert review."""
        return AuditService.log_action(
            db=db,
            action="review_alert",
            action_category="fraud_detection",
            target_type="fraud_alert",
            target_id=str(alert_id),
            target_name=f"Alert {alert_id}",
            actor_id=actor_id,
            metadata={"decision": decision, "notes": notes}
        )
    
    @staticmethod
    def log_rule_modification(
        db: Session,
        actor_id: int,
        rule_id: str,
        action_type: str,  # create, update, delete
        changes_before: Optional[Dict[str, Any]] = None,
        changes_after: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log rule creation, modification, or deletion."""
        return AuditService.log_action(
            db=db,
            action=f"{action_type}_rule",
            action_category="rule_management",
            target_type="fraud_rule",
            target_id=rule_id,
            target_name=f"Rule {rule_id}",
            actor_id=actor_id,
            changes_before=changes_before,
            changes_after=changes_after,
        )
    
    @staticmethod
    def log_model_training(
        db: Session,
        actor_id: Optional[int],
        model_version: str,
        dataset_id: str,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log model training."""
        return AuditService.log_action(
            db=db,
            action="train_model",
            action_category="ml_model",
            target_type="ml_model",
            target_id=model_version,
            target_name=f"Model {model_version}",
            actor_id=actor_id,
            status="success" if success else "failure",
            metadata={"dataset_id": dataset_id, "metrics": metrics}
        )
    
    @staticmethod
    def log_batch_import(
        db: Session,
        actor_id: Optional[int],
        row_count: int,
        idempotency_key: str,
    ) -> AuditLog:
        """Log batch import of transactions."""
        return AuditService.log_action(
            db=db,
            action="bulk_import_transactions",
            action_category="transaction",
            target_type="batch_import",
            target_id=idempotency_key,
            target_name=f"Batch import {idempotency_key}",
            actor_id=actor_id,
            metadata={"row_count": row_count, "idempotency_key": idempotency_key}
        )
    
    # ===== ALERT-SPECIFIC AUDIT LOGGING =====
    
    @staticmethod
    def log_alert_event(
        db: Session,
        alert_id: int,
        event_type: str,
        analyst_id: int,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        status_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Log alert-related events for compliance.
        
        Args:
            db: Database session
            alert_id: Alert ID
            event_type: Type of event (CREATED, STATUS_CHANGED, DECISION_RECORDED, REVIEWED, ESCALATED)
            analyst_id: Analyst ID who performed the action
            details: Additional event details (previous_status, new_status, decision, etc.)
            status: Event status (success or failure)
            status_message: Error message if event failed
        
        Returns:
            AuditLog entry
        """
        event_map = {
            "CREATED": "Alert created",
            "STATUS_CHANGED": "Alert status changed",
            "DECISION_RECORDED": "Analyst decision recorded",
            "REVIEWED": "Alert marked for review",
            "ESCALATED": "Alert escalated",
        }
        
        action_description = event_map.get(event_type, event_type)
        
        return AuditService.log_action(
            db=db,
            action=f"alert_{event_type.lower()}",
            action_category="alert_management",
            target_type="fraud_alert",
            target_id=str(alert_id),
            target_name=f"Alert {alert_id}",
            actor_id=analyst_id,
            status=status,
            status_message=status_message,
            metadata={"event_type": event_type, "details": details or {}}
        )
    
    @staticmethod
    def log_alert_status_change(
        db: Session,
        alert_id: int,
        old_status: str,
        new_status: str,
        analyst_id: int,
    ) -> AuditLog:
        """
        Log alert status transition.
        
        Args:
            db: Database session
            alert_id: Alert ID
            old_status: Previous status
            new_status: New status
            analyst_id: Analyst who changed the status
        
        Returns:
            AuditLog entry
        """
        return AuditService.log_alert_event(
            db=db,
            alert_id=alert_id,
            event_type="STATUS_CHANGED",
            analyst_id=analyst_id,
            details={
                "previous_status": old_status,
                "new_status": new_status,
            }
        )
    
    @staticmethod
    def log_analyst_decision(
        db: Session,
        alert_id: int,
        decision: str,
        justification: str,
        analyst_id: int,
    ) -> AuditLog:
        """
        Log analyst decision on an alert.
        
        Args:
            db: Database session
            alert_id: Alert ID
            decision: Decision type (APPROVED, REJECTED, NEEDS_REVIEW)
            justification: Reasoning for the decision
            analyst_id: Analyst who made the decision
        
        Returns:
            AuditLog entry
        """
        return AuditService.log_alert_event(
            db=db,
            alert_id=alert_id,
            event_type="DECISION_RECORDED",
            analyst_id=analyst_id,
            details={
                "decision": decision,
                "justification": justification[:500],  # Truncate for storage
            }
        )
    
    @staticmethod
    @staticmethod
    def get_alert_history(
        session: Session,
        alert_id: int,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get all audit events for an alert.
        
        Args:
            session: Database session
            alert_id: Alert ID
            limit: Maximum number of events to return
        
        Returns:
            List of AuditLog entries for this alert
        """
        return session.query(AuditLog).filter(
            AuditLog.target_type == "fraud_alert",
            AuditLog.target_id == str(alert_id)
        ).order_by(
            AuditLog.action_timestamp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_analyst_actions(
        db: Session,
        analyst_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_category: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get all actions performed by a specific analyst.
        
        Args:
            db: Database session
            analyst_id: Analyst user ID
            start_date: Filter start date (default: 30 days ago)
            end_date: Filter end date (default: now)
            action_category: Filter by action category (alert_management, etc.)
            limit: Maximum number of actions to return
        
        Returns:
            List of AuditLog entries for this analyst
        """
        if not start_date:
            from datetime import timedelta
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        query = db.query(AuditLog).filter(
            AuditLog.actor_id == analyst_id,
            AuditLog.action_timestamp >= start_date,
            AuditLog.action_timestamp <= end_date
        )
        
        if action_category:
            query = query.filter(AuditLog.action_category == action_category)
        
        return query.order_by(
            AuditLog.action_timestamp.desc()
        ).limit(limit).all()
