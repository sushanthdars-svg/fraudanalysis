#!/usr/bin/env python
"""Script to export data to CSV files."""

import os
import sys
import logging
import csv
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.absolute().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Transaction, Alert, AuditLog
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def export_transactions(
    output_dir: str = "exports",
    start_date: datetime = None,
    end_date: datetime = None,
    status_filter: str = None
) -> bool:
    """
    Export transactions to CSV.
    
    Args:
        output_dir: Directory to store exports
        start_date: Start date filter
        end_date: End date filter
        status_filter: Transaction status filter
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Build query
        query = session.query(Transaction)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if status_filter:
            query = query.filter(Transaction.status == status_filter)
        
        transactions = query.all()
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"transactions_{timestamp}.csv"
        
        logger.info(f"Exporting {len(transactions)} transactions to {export_file}")
        
        with open(export_file, 'w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'transaction_id', 'customer_id', 'merchant_id', 'transaction_date',
                    'amount', 'currency', 'transaction_type', 'status', 'location',
                    'ip_address', 'device_id', 'mcc_code'
                ]
            )
            writer.writeheader()
            
            for txn in transactions:
                writer.writerow({
                    'transaction_id': txn.transaction_id,
                    'customer_id': txn.customer_id,
                    'merchant_id': txn.merchant_id,
                    'transaction_date': txn.transaction_date,
                    'amount': txn.amount,
                    'currency': txn.currency,
                    'transaction_type': txn.transaction_type,
                    'status': txn.status,
                    'location': txn.location,
                    'ip_address': txn.ip_address,
                    'device_id': txn.device_id,
                    'mcc_code': txn.mcc_code
                })
        
        logger.info(f"✅ Exported {len(transactions)} transactions to {export_file}")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {str(e)}")
        return False


def export_alerts(
    output_dir: str = "exports",
    start_date: datetime = None,
    end_date: datetime = None,
    status_filter: str = None,
    severity_filter: str = None
) -> bool:
    """
    Export alerts to CSV.
    
    Args:
        output_dir: Directory to store exports
        start_date: Start date filter
        end_date: End date filter
        status_filter: Alert status filter
        severity_filter: Alert severity filter
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Build query
        query = session.query(Alert)
        
        if start_date:
            query = query.filter(Alert.created_at >= start_date)
        if end_date:
            query = query.filter(Alert.created_at <= end_date)
        if status_filter:
            query = query.filter(Alert.status == status_filter)
        if severity_filter:
            query = query.filter(Alert.severity == severity_filter)
        
        alerts = query.all()
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"alerts_{timestamp}.csv"
        
        logger.info(f"Exporting {len(alerts)} alerts to {export_file}")
        
        with open(export_file, 'w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'alert_id', 'transaction_id', 'customer_id', 'alert_type',
                    'severity', 'risk_score', 'status', 'created_at'
                ]
            )
            writer.writeheader()
            
            for alert in alerts:
                writer.writerow({
                    'alert_id': alert.alert_id,
                    'transaction_id': alert.transaction_id,
                    'customer_id': alert.customer_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'risk_score': alert.risk_score,
                    'status': alert.status,
                    'created_at': alert.created_at
                })
        
        logger.info(f"✅ Exported {len(alerts)} alerts to {export_file}")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {str(e)}")
        return False


def export_audit_logs(
    output_dir: str = "exports",
    start_date: datetime = None,
    end_date: datetime = None,
    action_filter: str = None
) -> bool:
    """
    Export audit logs to CSV.
    
    Args:
        output_dir: Directory to store exports
        start_date: Start date filter
        end_date: End date filter
        action_filter: Action type filter
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Build query
        query = session.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        logs = query.all()
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"audit_logs_{timestamp}.csv"
        
        logger.info(f"Exporting {len(logs)} audit logs to {export_file}")
        
        with open(export_file, 'w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'actor_id', 'action', 'target_type', 'target_id',
                    'details', 'ip_address', 'created_at'
                ]
            )
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    'actor_id': log.actor_id,
                    'action': log.action,
                    'target_type': log.target_type,
                    'target_id': log.target_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at
                })
        
        logger.info(f"✅ Exported {len(logs)} audit logs to {export_file}")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Export Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Transactions export
    txn_parser = subparsers.add_parser("transactions", help="Export transactions")
    txn_parser.add_argument("--output-dir", default="exports", help="Output directory")
    txn_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    txn_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    txn_parser.add_argument("--status", help="Transaction status filter")
    
    # Alerts export
    alert_parser = subparsers.add_parser("alerts", help="Export alerts")
    alert_parser.add_argument("--output-dir", default="exports", help="Output directory")
    alert_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    alert_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    alert_parser.add_argument("--status", help="Alert status filter")
    alert_parser.add_argument("--severity", help="Severity filter")
    
    # Audit logs export
    audit_parser = subparsers.add_parser("audit_logs", help="Export audit logs")
    audit_parser.add_argument("--output-dir", default="exports", help="Output directory")
    audit_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    audit_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    audit_parser.add_argument("--action", help="Action type filter")
    
    args = parser.parse_args()
    
    if args.command == "transactions":
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
        success = export_transactions(args.output_dir, start_date, end_date, args.status)
        sys.exit(0 if success else 1)
    elif args.command == "alerts":
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
        success = export_alerts(args.output_dir, start_date, end_date, args.status, args.severity)
        sys.exit(0 if success else 1)
    elif args.command == "audit_logs":
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
        success = export_audit_logs(args.output_dir, start_date, end_date, args.action)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)
