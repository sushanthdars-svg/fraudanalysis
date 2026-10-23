"""Admin-only access to persisted audit events and period summaries."""

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.permissions import UserRole
from app.core.security import require_role
from app.db.database import get_db
from app.models import AuditLog, User


router = APIRouter(prefix="/api/audit-logs", tags=["audit logs"])


def period_query(db: Session, start_date: date | None, end_date: date | None):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, detail="Start date must not be after end date")
    query = db.query(AuditLog)
    if start_date:
        query = query.filter(AuditLog.action_timestamp >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(
            AuditLog.action_timestamp <= datetime.combine(end_date, time.max)
        )
    return query


@router.get("")
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    actor: str | None = None,
    action: str | None = None,
    target_entity: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    query = period_query(db, start_date, end_date)
    if actor:
        query = query.join(AuditLog.actor).filter(User.email == actor.strip().lower())
    if action:
        prefix = action.lower()
        query = query.filter(or_(
            AuditLog.action == prefix,
            AuditLog.action.startswith(prefix + "_", autoescape=True),
        ))
    if target_entity:
        query = query.filter(AuditLog.target_type == target_entity.lower())
    total = query.count()
    events = (
        query.options(joinedload(AuditLog.actor))
        .order_by(AuditLog.action_timestamp.desc(), AuditLog.id.desc())
        .offset(skip).limit(limit).all()
    )
    return {
        "total": total,
        "items": [{
            "id": event.id,
            "timestamp": event.action_timestamp,
            "actor": event.actor.email if event.actor else "System",
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "status": event.action_status,
            "success": event.action_status == "success",
            "details": event.status_message or "",
            "changes_before": event.changes_before,
            "changes_after": event.changes_after,
        } for event in events],
    }


@router.get("/compliance-report")
def compliance_report(
    report_type: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    query = period_query(db, start_date, end_date)
    if report_type == "user_access":
        query = query.filter(AuditLog.action_category == "authentication")
    elif report_type == "data_changes":
        query = query.filter(or_(
            AuditLog.action.startswith("create_"),
            AuditLog.action.startswith("update_"),
            AuditLog.action.startswith("delete_"),
        ))
    elif report_type in {"alerts_review", "rule_modifications", "model_updates"}:
        targets = {
            "alerts_review": ["fraud_alert"],
            "rule_modifications": ["fraud_rule"],
            "model_updates": ["model", "ml_model"],
        }
        query = query.filter(AuditLog.target_type.in_(targets[report_type]))
    elif report_type == "security_events":
        query = query.filter(or_(
            AuditLog.action_category == "authentication",
            AuditLog.action_status != "success",
        ))
    else:
        raise HTTPException(422, detail="Unknown report type")
    return {
        "summary": {
            "total_events": query.count(),
            "unique_users": query.with_entities(func.count(func.distinct(AuditLog.actor_id))).scalar(),
            "failed_actions": query.filter(AuditLog.action_status == "failure").count(),
            "exceptions": query.filter(AuditLog.action_status.notin_(["success", "failure"])).count(),
        },
        "findings": [],
    }
