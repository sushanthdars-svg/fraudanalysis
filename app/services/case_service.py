"""
Case Management Service - Manages fraud investigation cases.
Handles case creation, updates, and investigation notes.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.case import InvestigationCase, CaseNote
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class CaseService:
    """
    Manages investigation cases for fraud alerts.
    
    Case lifecycle:
    1. OPEN - Created from high-risk alert
    2. UNDER_INVESTIGATION - Actively being investigated
    3. CLOSED - Investigation complete with outcome
    4. ESCALATED - Escalated to management/external authorities
    """
    
    @staticmethod
    def create_case_from_alert(
        session: Session,
        alert_id: int,
        case_type: str,
        assigned_to: int,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an investigation case from a fraud alert.
        
        Args:
            session: Database session
            alert_id: Alert ID
            case_type: FRAUD_CONFIRMED, SUSPICIOUS, FALSE_POSITIVE, UNDER_INVESTIGATION
            assigned_to: Analyst user ID to assign case
            summary: Initial summary of the case
        
        Returns:
            Dictionary with case details
        
        Raises:
            ValueError: If alert not found or case already exists
        """
        try:
            # Verify alert exists
            alert = session.query(FraudAlert).filter(
                FraudAlert.id == alert_id
            ).first()
            
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Check if case already exists for this alert
            existing_case = session.query(InvestigationCase).filter(
                InvestigationCase.alert_id == alert_id
            ).first()
            
            if existing_case:
                raise ValueError(f"Case already exists for alert {alert_id}")
            
            # Create case
            case = InvestigationCase(
                alert_id=alert_id,
                transaction_id=alert.transaction_id,
                customer_id=alert.customer_id,
                case_type=case_type,
                case_status="open",
                assigned_to=assigned_to,
                summary=summary,
                case_created_at=datetime.utcnow(),
            )
            
            session.add(case)
            session.commit()
            
            logger.info(
                f"Created investigation case: alert={alert_id}, "
                f"type={case_type}, assigned_to={assigned_to}"
            )
            
            return CaseService._format_case_response(case)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating case from alert: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_case(session: Session, case_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a case by ID.
        
        Args:
            session: Database session
            case_id: Case ID
        
        Returns:
            Case details or None if not found
        """
        case = session.query(InvestigationCase).filter(
            InvestigationCase.id == case_id
        ).first()
        
        if not case:
            return None
        
        return CaseService._format_case_response(case)
    
    @staticmethod
    def get_case_by_alert(session: Session, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a case by alert ID.
        
        Args:
            session: Database session
            alert_id: Alert ID
        
        Returns:
            Case details or None if not found
        """
        case = session.query(InvestigationCase).filter(
            InvestigationCase.alert_id == alert_id
        ).first()
        
        if not case:
            return None
        
        return CaseService._format_case_response(case)
    
    @staticmethod
    def get_active_cases(
        session: Session,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get all active cases (not closed).
        
        Args:
            session: Database session
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (cases list, total count)
        """
        query = session.query(InvestigationCase).filter(
            InvestigationCase.case_status.in_(["open", "under_investigation", "escalated"])
        ).order_by(
            desc(InvestigationCase.case_created_at)
        )
        
        total = query.count()
        cases = query.limit(limit).offset(offset).all()
        
        return (
            [CaseService._format_case_response(c) for c in cases],
            total
        )
    
    @staticmethod
    def get_cases_by_analyst(
        session: Session,
        analyst_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get cases assigned to a specific analyst.
        
        Args:
            session: Database session
            analyst_id: Analyst user ID
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (cases list, total count)
        """
        query = session.query(InvestigationCase).filter(
            InvestigationCase.assigned_to == analyst_id
        ).order_by(
            desc(InvestigationCase.case_created_at)
        )
        
        total = query.count()
        cases = query.limit(limit).offset(offset).all()
        
        return (
            [CaseService._format_case_response(c) for c in cases],
            total
        )
    
    @staticmethod
    def update_case_status(
        session: Session,
        case_id: int,
        new_status: str,
        summary: Optional[str] = None,
        findings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update case status.
        
        Args:
            session: Database session
            case_id: Case ID
            new_status: New status (open, under_investigation, closed, escalated)
            summary: Updated summary
            findings: Investigation findings
        
        Returns:
            Updated case details
        
        Raises:
            ValueError: If case not found or invalid status
        """
        try:
            case = session.query(InvestigationCase).filter(
                InvestigationCase.id == case_id
            ).first()
            
            if not case:
                raise ValueError(f"Case {case_id} not found")
            
            valid_statuses = ["open", "under_investigation", "closed", "escalated"]
            if new_status not in valid_statuses:
                raise ValueError(f"Invalid status: {new_status}")
            
            case.case_status = new_status
            
            if summary:
                case.summary = summary
            
            if findings:
                case.findings = findings
            
            if new_status == "closed":
                case.case_closed_at = datetime.utcnow()
            
            session.commit()
            
            logger.info(f"Updated case {case_id} status to {new_status}")
            
            return CaseService._format_case_response(case)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating case status: {e}", exc_info=True)
            raise
    
    @staticmethod
    def add_case_note(
        session: Session,
        case_id: int,
        note_text: str,
        analyst_id: int,
        note_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Add a note to a case.
        
        Args:
            session: Database session
            case_id: Case ID
            note_text: Note content
            analyst_id: Analyst user ID
            note_type: Type of note (general, finding, action, decision)
        
        Returns:
            Dictionary with note details
        
        Raises:
            ValueError: If case not found
        """
        try:
            # Verify case exists
            case = session.query(InvestigationCase).filter(
                InvestigationCase.id == case_id
            ).first()
            
            if not case:
                raise ValueError(f"Case {case_id} not found")
            
            # Create note
            note = CaseNote(
                case_id=case_id,
                analyst_id=analyst_id,
                note_text=note_text,
                note_type=note_type,
                created_at=datetime.utcnow(),
            )
            
            session.add(note)
            session.commit()
            
            logger.info(f"Added note to case {case_id}")
            
            return {
                "note_id": note.id,
                "case_id": case_id,
                "analyst_id": analyst_id,
                "note_text": note_text,
                "note_type": note_type,
                "created_at": note.created_at,
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding case note: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_case_notes(
        session: Session,
        case_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get notes for a case.
        
        Args:
            session: Database session
            case_id: Case ID
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (notes list, total count)
        """
        query = session.query(CaseNote).filter(
            CaseNote.case_id == case_id
        ).order_by(
            desc(CaseNote.created_at)
        )
        
        total = query.count()
        notes = query.limit(limit).offset(offset).all()
        
        return (
            [CaseService._format_note_response(n) for n in notes],
            total
        )
    
    @staticmethod
    @staticmethod
    def escalate_case(
        session: Session,
        case_id: int,
        escalated_to: int,
        escalation_reason: str,
        escalated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Escalate a case to management.
        
        Args:
            session: Database session
            case_id: Case ID
            escalated_to: Manager user ID
            escalation_reason: Escalation reason
            escalated_by: Analyst ID performing escalation
        
        Returns:
            Updated case details
        """
        try:
            case = session.query(InvestigationCase).filter(
                InvestigationCase.id == case_id
            ).first()
            
            if not case:
                raise ValueError(f"Case {case_id} not found")
            
            case.escalated = True
            case.escalation_reason = escalation_reason
            case.escalated_to = escalated_to
            case.case_status = "escalated"
            
            session.commit()
            
            logger.info(f"Escalated case {case_id} to user {escalated_to}")
            
            return CaseService._format_case_response(case)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error escalating case: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _format_case_response(case: InvestigationCase) -> Dict[str, Any]:
        """Format case model to response dictionary."""
        return {
            "case_id": case.id,
            "alert_id": case.alert_id,
            "transaction_id": case.transaction_id,
            "customer_id": case.customer_id,
            "case_type": case.case_type,
            "case_status": case.case_status,
            "assigned_to": case.assigned_to,
            "summary": case.summary,
            "findings": case.findings,
            "case_created_at": case.case_created_at,
            "case_closed_at": case.case_closed_at,
            "case_notes": case.case_notes,
            "escalated": case.escalated,
            "escalation_reason": case.escalation_reason,
            "escalated_to": case.escalated_to,
        }
    
    @staticmethod
    def _format_note_response(note: CaseNote) -> Dict[str, Any]:
        """Format note model to response dictionary."""
        return {
            "note_id": note.id,
            "case_id": note.case_id,
            "analyst_id": note.analyst_id,
            "note_text": note.note_text,
            "note_type": note.note_type,
            "created_at": note.created_at,
        }
