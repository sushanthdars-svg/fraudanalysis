"""
Alert Service - Manages creation and updates of fraud alerts.
Handles alert lifecycle from creation to resolution.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.fraud_alert import FraudAlert, FraudAssessment
from app.models.transaction import Transaction
from app.models.user import User

logger = logging.getLogger(__name__)


class AlertService:
    """
    Manages fraud alert lifecycle.
    
    Alert lifecycle:
    1. PENDING - Created after assessment
    2. UNDER_REVIEW - Analyst is reviewing
    3. RESOLVED - Final decision made (approved/rejected/escalated)
    """
    
    # Priority mapping based on risk score
    PRIORITY_MAPPING = {
        "HIGH": (71, 100),    # risk_score > 70
        "MEDIUM": (31, 70),   # risk_score 31-70
        "LOW": (0, 30),       # risk_score < 30
    }
    
    # Alert type mapping
    ALERT_TYPE_MAPPING = {
        "rule_triggered": "RULE_TRIGGERED",
        "ml_predicted": "ML_PREDICTED",
        "combined": "COMBINED",
    }
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        "pending": ["under_review", "dismissed"],
        "under_review": ["resolved", "dismissed"],
        "resolved": [],
        "dismissed": [],
    }
    
    @staticmethod
    def create_fraud_alert(
        session: Session,
        transaction_id: int,
        customer_id: int,
        assessment_id: int,
        risk_score: float,
        risk_level: str,
        alert_reason: str,
        triggered_rules_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new fraud alert.
        
        Args:
            session: Database session
            transaction_id: Transaction ID (database primary key)
            customer_id: Customer ID
            assessment_id: Associated FraudAssessment ID
            risk_score: Risk score (0-100)
            risk_level: Risk level (LOW/MEDIUM/HIGH)
            alert_reason: Reason for alert creation
            triggered_rules_summary: Summary of triggered rules (optional)
        
        Returns:
            Dictionary with alert details
        
        Raises:
            ValueError: If assessment or transaction not found
        """
        try:
            # Verify assessment exists
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.id == assessment_id
            ).first()
            
            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")
            
            # Verify transaction exists
            transaction = session.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Determine severity based on risk score
            if risk_score >= 71:
                severity = "high"
            elif risk_score >= 31:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert
            alert = FraudAlert(
                transaction_id=transaction_id,
                customer_id=customer_id,
                assessment_id=assessment_id,
                alert_severity=severity,
                alert_status="pending",
                alert_reason=alert_reason,
                triggered_rules_summary=triggered_rules_summary,
                alert_created_at=datetime.utcnow(),
            )
            
            session.add(alert)
            session.commit()
            
            logger.info(
                f"Created fraud alert: transaction={transaction_id}, "
                f"assessment={assessment_id}, severity={severity}"
            )
            
            return AlertService._format_alert_response(alert)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating fraud alert: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_alert(session: Session, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an alert by ID.
        
        Args:
            session: Database session
            alert_id: Alert ID
        
        Returns:
            Alert details or None if not found
        """
        alert = session.query(FraudAlert).filter(
            FraudAlert.id == alert_id
        ).first()
        
        if not alert:
            return None
        
        return AlertService._format_alert_response(alert)
    
    @staticmethod
    def get_pending_alerts(
        session: Session,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get all pending alerts (not yet resolved).
        
        Args:
            session: Database session
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_status == "pending"
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_alerts_by_status(
        session: Session,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get alerts filtered by status.
        
        Args:
            session: Database session
            status: Alert status (pending, under_review, resolved, dismissed)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        valid_statuses = ["pending", "under_review", "resolved", "dismissed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_status == status
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_alerts_by_customer(
        session: Session,
        customer_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get alerts for a specific customer.
        
        Args:
            session: Database session
            customer_id: Customer ID
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        query = session.query(FraudAlert).filter(
            FraudAlert.customer_id == customer_id
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def update_alert_status(
        session: Session,
        alert_id: int,
        new_status: str,
        reviewed_by_user_id: Optional[int] = None,
        review_decision: Optional[str] = None,
        review_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update alert status and review information.
        
        Args:
            session: Database session
            alert_id: Alert ID
            new_status: New status (pending, under_review, resolved, dismissed)
            reviewed_by_user_id: User ID of reviewer (optional)
            review_decision: Review decision (approved, rejected, escalated, etc.)
            review_notes: Additional review notes
        
        Returns:
            Updated alert details
        
        Raises:
            ValueError: If alert not found or invalid status transition
        """
        try:
            alert = session.query(FraudAlert).filter(
                FraudAlert.id == alert_id
            ).first()
            
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Validate status transition
            valid_next_statuses = AlertService.VALID_TRANSITIONS.get(
                alert.alert_status, []
            )
            if new_status not in valid_next_statuses:
                raise ValueError(
                    f"Invalid status transition from {alert.alert_status} to {new_status}. "
                    f"Valid transitions: {valid_next_statuses}"
                )
            
            # Update status and review info
            alert.alert_status = new_status
            
            if review_decision:
                alert.review_decision = review_decision
            
            if review_notes:
                alert.review_notes = review_notes
            
            if reviewed_by_user_id:
                alert.reviewed_by = reviewed_by_user_id
                alert.review_timestamp = datetime.utcnow()
            
            session.commit()
            
            logger.info(
                f"Updated alert {alert_id}: status={new_status}, "
                f"decision={review_decision}, reviewed_by={reviewed_by_user_id}"
            )
            
            return AlertService._format_alert_response(alert)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating alert status: {e}", exc_info=True)
            raise
    
    @staticmethod
    def dismiss_alert(
        session: Session,
        alert_id: int,
        reviewed_by_user_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Dismiss an alert (false positive).
        
        Args:
            session: Database session
            alert_id: Alert ID
            reviewed_by_user_id: User ID of reviewer
            reason: Reason for dismissal
        
        Returns:
            Updated alert details
        """
        return AlertService.update_alert_status(
            session=session,
            alert_id=alert_id,
            new_status="dismissed",
            reviewed_by_user_id=reviewed_by_user_id,
            review_decision="dismissed",
            review_notes=reason
        )
    
    @staticmethod
    def approve_alert(
        session: Session,
        alert_id: int,
        reviewed_by_user_id: int,
        action_taken: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve an alert and mark as resolved.
        
        Args:
            session: Database session
            alert_id: Alert ID
            reviewed_by_user_id: User ID of reviewer
            action_taken: Action taken (blocked_card, frozen_account, contacted_customer, etc.)
            notes: Additional notes
        
        Returns:
            Updated alert details
        """
        return AlertService.update_alert_status(
            session=session,
            alert_id=alert_id,
            new_status="resolved",
            reviewed_by_user_id=reviewed_by_user_id,
            review_decision="approved",
            review_notes=f"Action: {action_taken}. {notes or ''}"
        )
    
    @staticmethod
    def _format_alert_response(alert: FraudAlert) -> Dict[str, Any]:
        """Format alert model to response dictionary."""
        # Get assessment data for risk score and level
        assessment_data = {
            "risk_score": 0.0,
            "risk_level": "low",
            "ml_score": None
        }
        
        if alert.assessment:
            assessment_data["risk_score"] = float(alert.assessment.risk_score) if alert.assessment.risk_score else 0.0
            assessment_data["risk_level"] = alert.assessment.risk_category if alert.assessment.risk_category else "low"
            assessment_data["ml_score"] = float(alert.assessment.ml_score) if alert.assessment.ml_score else None
        
        return {
            "alert_id": alert.id,
            "transaction_id": alert.transaction_id,
            "customer_id": alert.customer_id,
            "assessment_id": alert.assessment_id,
            "risk_score": assessment_data["risk_score"],
            "risk_level": assessment_data["risk_level"],
            "ml_score": assessment_data["ml_score"],
            "alert_severity": alert.alert_severity,
            "alert_status": alert.alert_status,
            "alert_reason": alert.alert_reason,
            "triggered_rules_summary": alert.triggered_rules_summary,
            "reviewed_by": alert.reviewed_by,
            "review_timestamp": alert.review_timestamp,
            "review_decision": alert.review_decision,
            "review_notes": alert.review_notes,
            "alert_created_at": alert.alert_created_at,
            "created_at": alert.alert_created_at,  # For API compatibility
            "alert_resolved_at": alert.alert_resolved_at if hasattr(alert, "alert_resolved_at") else None,
        }
    
    @staticmethod
    def get_alert_statistics(session: Session) -> Dict[str, Any]:
        """
        Get alert statistics for dashboard.
        
        Args:
            session: Database session
        
        Returns:
            Dictionary with alert statistics
        """
        total_alerts = session.query(FraudAlert).count()
        
        status_counts = {}
        for status in ["pending", "under_review", "resolved", "dismissed"]:
            count = session.query(FraudAlert).filter(
                FraudAlert.alert_status == status
            ).count()
            status_counts[status] = count
        
        severity_counts = {}
        for severity in ["low", "medium", "high"]:
            count = session.query(FraudAlert).filter(
                FraudAlert.alert_severity == severity
            ).count()
            severity_counts[severity] = count
        
        return {
            "total_alerts": total_alerts,
            "status_counts": status_counts,
            "severity_counts": severity_counts,
        }
    
    @staticmethod
    def record_analyst_decision(
        session: Session,
        alert_id: int,
        decision: str,
        justification: str,
        analyst_id: int
    ) -> Dict[str, Any]:
        """
        Record analyst's decision on an alert.
        
        Args:
            session: Database session
            alert_id: Alert ID
            decision: APPROVED (fraud confirmed), REJECTED (not fraud), NEEDS_REVIEW
            justification: Detailed reasoning for decision
            analyst_id: Analyst user ID
        
        Returns:
            Updated alert with decision
        
        Raises:
            ValueError: If alert not found or invalid decision
        """
        valid_decisions = ["APPROVED", "REJECTED", "NEEDS_REVIEW"]
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision: {decision}. Must be one of {valid_decisions}")
        
        alert = session.query(FraudAlert).filter(
            FraudAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        try:
            # Update alert with decision
            if decision == "APPROVED":
                alert.review_decision = "approved"
                alert.alert_status = "resolved"
            elif decision == "REJECTED":
                alert.review_decision = "rejected"
                alert.alert_status = "resolved"
            elif decision == "NEEDS_REVIEW":
                alert.review_decision = "needs_review"
                alert.alert_status = "under_review"
            
            alert.review_notes = justification
            alert.reviewed_by = analyst_id
            alert.review_timestamp = datetime.utcnow()
            
            session.commit()
            
            logger.info(
                f"Analyst {analyst_id} recorded {decision} decision on alert {alert_id}"
            )
            
            return AlertService._format_alert_response(alert)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording analyst decision: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_alerts_by_priority(
        session: Session,
        priority: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get alerts filtered by priority (severity).
        
        Args:
            session: Database session
            priority: Alert priority/severity (low, medium, high)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}")
        
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_severity == priority
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_analyst_alerts(
        session: Session,
        analyst_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get alerts reviewed by a specific analyst.
        
        Args:
            session: Database session
            analyst_id: Analyst user ID
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        query = session.query(FraudAlert).filter(
            FraudAlert.reviewed_by == analyst_id
        ).order_by(
            desc(FraudAlert.review_timestamp)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def search_alerts(
        session: Session,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Search alerts by reason/notes with optional filters.
        
        Args:
            session: Database session
            query_text: Search query text
            filters: Dictionary of filters (status, severity, analyst_id, etc.)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (alerts list, total count)
        """
        query = session.query(FraudAlert)
        
        # Text search
        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.filter(
                and_(
                    FraudAlert.alert_reason.ilike(search_pattern) |
                    FraudAlert.review_notes.ilike(search_pattern)
                )
            )
        
        # Apply filters
        filters = filters or {}
        if "status" in filters:
            query = query.filter(FraudAlert.alert_status == filters["status"])
        if "severity" in filters:
            query = query.filter(FraudAlert.alert_severity == filters["severity"])
        if "analyst_id" in filters:
            query = query.filter(FraudAlert.reviewed_by == filters["analyst_id"])
        if "customer_id" in filters:
            query = query.filter(FraudAlert.customer_id == filters["customer_id"])
        
        query = query.order_by(desc(FraudAlert.alert_created_at))
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    # ===== PAGINATED VERSIONS FOR API =====
    
    @staticmethod
    def get_pending_alerts_paginated(
        session: Session,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get pending alerts with pagination."""
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_status == "pending"
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_analyst_alerts_paginated(
        session: Session,
        analyst_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get alerts assigned to analyst with pagination."""
        query = session.query(FraudAlert).filter(
            FraudAlert.reviewed_by == analyst_id
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_alerts_by_status_paginated(
        session: Session,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get alerts by status with pagination."""
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_status == status
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def get_alerts_by_priority_paginated(
        session: Session,
        priority: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get alerts by priority with pagination."""
        query = session.query(FraudAlert).filter(
            FraudAlert.alert_severity == priority.lower()
        ).order_by(
            desc(FraudAlert.alert_created_at)
        )
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
    
    @staticmethod
    def search_alerts_paginated(
        session: Session,
        query_text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search alerts with pagination."""
        query = session.query(FraudAlert)
        
        # Text search
        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.filter(
                and_(
                    FraudAlert.alert_reason.ilike(search_pattern) |
                    FraudAlert.review_notes.ilike(search_pattern)
                )
            )
        
        # Apply filters
        filters = filters or {}
        if filters.get("status"):
            query = query.filter(FraudAlert.alert_status == filters["status"])
        if filters.get("severity"):
            query = query.filter(FraudAlert.alert_severity == filters["severity"])
        if filters.get("priority"):
            query = query.filter(FraudAlert.alert_severity == filters["priority"])
        if filters.get("min_risk_score") is not None:
            query = query.filter(FraudAlert.risk_score >= filters["min_risk_score"])
        if filters.get("max_risk_score") is not None:
            query = query.filter(FraudAlert.risk_score <= filters["max_risk_score"])
        
        query = query.order_by(desc(FraudAlert.alert_created_at))
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return (
            [AlertService._format_alert_response(a) for a in alerts],
            total
        )
