"""
Analytics Service - Comprehensive fraud detection metrics and analytics.
Provides transaction, alert, customer, and anomaly detection analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func, desc

from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert, FraudAssessment
from app.models.customer import Customer
from app.models.case import InvestigationCase
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Comprehensive analytics service for fraud detection metrics.
    Provides transaction, alert, customer, and anomaly detection analytics.
    """
    
    # Risk level thresholds (0-100)
    RISK_THRESHOLDS = {
        "LOW": (0, 30),
        "MEDIUM": (31, 70),
        "HIGH": (71, 100),
    }
    
    # Anomaly detection thresholds
    ANOMALY_THRESHOLDS = {
        "volume_spike": 1.5,  # 50% above average
        "velocity_threshold": 5,  # 5 transactions in 1 hour
        "large_transaction": 10000,  # Amount in base currency
    }
    
    @staticmethod
    def get_transaction_statistics(
        session: Session,
        days: int = 30,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive transaction statistics.
        
        Args:
            session: Database session
            days: Number of days to analyze
            customer_id: Optional customer filter
        
        Returns:
            Dictionary with transaction statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        )
        
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        
        transactions = query.options(selectinload(Transaction.fraud_assessments)).all()
        
        if not transactions:
            return {
                "total_transactions": 0,
                "total_volume": Decimal("0"),
                "average_amount": Decimal("0"),
                "high_risk_transactions": 0,
                "medium_risk_transactions": 0,
                "low_risk_transactions": 0,
                "min_amount": Decimal("0"),
                "max_amount": Decimal("0"),
                "days": days,
            }
        
        # Count transactions by risk category
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        total_volume = Decimal("0")
        
        for txn in transactions:
            total_volume += txn.amount
            
            # Get assessment for this transaction
            assessment = txn.fraud_assessments[0] if txn.fraud_assessments else None
            
            if assessment:
                risk_category = assessment.risk_category.upper()
                if risk_category == "HIGH":
                    high_risk_count += 1
                elif risk_category == "MEDIUM":
                    medium_risk_count += 1
                elif risk_category == "LOW":
                    low_risk_count += 1
        
        avg_amount = total_volume / len(transactions) if transactions else Decimal("0")
        
        amounts = [t.amount for t in transactions]
        min_amount = min(amounts) if amounts else Decimal("0")
        max_amount = max(amounts) if amounts else Decimal("0")
        
        return {
            "total_transactions": len(transactions),
            "total_volume": float(total_volume),
            "average_amount": float(avg_amount),
            "high_risk_transactions": high_risk_count,
            "medium_risk_transactions": medium_risk_count,
            "low_risk_transactions": low_risk_count,
            "min_amount": float(min_amount),
            "max_amount": float(max_amount),
            "days": days,
        }
    
    @staticmethod
    def get_transaction_trends(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily transaction trends.
        
        Args:
            session: Database session
            days: Number of days to analyze
        
        Returns:
            List of daily trend data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        trends = []
        
        for i in range(days):
            date = cutoff_date + timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            transactions = session.query(Transaction).filter(
                and_(
                    Transaction.transaction_date >= date_start,
                    Transaction.transaction_date < date_end
                )
            ).all()
            
            total_volume = sum(t.amount for t in transactions) if transactions else Decimal("0")
            
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "transaction_count": len(transactions),
                "total_volume": float(total_volume),
                "average_amount": float(total_volume / len(transactions)) if transactions else 0,
            })
        
        return trends
    
    @staticmethod
    def get_risk_distribution(session: Session, days: int = 30) -> Dict[str, int]:
        """
        Get distribution of risk scores by category.
        
        Args:
            session: Database session
            days: Number of days to analyze
        
        Returns:
            Dictionary with risk category counts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        assessments = session.query(FraudAssessment).filter(
            FraudAssessment.assessment_timestamp >= cutoff_date
        ).all()
        
        distribution = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "total": len(assessments),
        }
        
        for assessment in assessments:
            category = assessment.risk_category.upper()
            if category == "HIGH":
                distribution["HIGH"] += 1
            elif category == "MEDIUM":
                distribution["MEDIUM"] += 1
            elif category == "LOW":
                distribution["LOW"] += 1
        
        return distribution
    
    @staticmethod
    def get_alert_statistics(
        session: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive alert statistics.
        
        Args:
            session: Database session
            days: Number of days to analyze
        
        Returns:
            Dictionary with alert statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        alerts = session.query(FraudAlert).filter(
            FraudAlert.created_at >= cutoff_date
        ).all()
        
        total_alerts = len(alerts)
        
        pending_count = sum(1 for a in alerts if a.alert_status == "pending")
        under_review_count = sum(1 for a in alerts if a.alert_status == "under_review")
        resolved_count = sum(1 for a in alerts if a.alert_status == "resolved")
        dismissed_count = sum(1 for a in alerts if a.alert_status == "dismissed")
        
        # Calculate approval and rejection rates
        approved_count = 0
        rejected_count = 0
        
        for alert in alerts:
            if alert.review_decision == "approved":
                approved_count += 1
            elif alert.review_decision == "rejected":
                rejected_count += 1
        
        total_resolved = approved_count + rejected_count
        approval_rate = (approved_count / total_resolved * 100) if total_resolved > 0 else 0
        rejection_rate = (rejected_count / total_resolved * 100) if total_resolved > 0 else 0
        
        # Calculate average review time
        review_times = []
        for alert in alerts:
            if alert.review_timestamp and alert.created_at:
                review_time = (alert.review_timestamp - alert.created_at).total_seconds() / 3600
                review_times.append(review_time)
        
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0
        
        return {
            "total_alerts": total_alerts,
            "pending_alerts": pending_count,
            "under_review_alerts": under_review_count,
            "resolved_alerts": resolved_count,
            "dismissed_alerts": dismissed_count,
            "approved_alerts": approved_count,
            "rejected_alerts": rejected_count,
            "approval_rate": approval_rate,
            "rejection_rate": rejection_rate,
            "average_review_time_hours": avg_review_time,
            "days": days,
        }
    
    @staticmethod
    def get_fraud_confirmed_rate(session: Session) -> float:
        """
        Calculate rate of approved fraud cases.
        
        Args:
            session: Database session
        
        Returns:
            Fraud confirmation rate (0-100)
        """
        all_alerts = session.query(FraudAlert).all()
        
        if not all_alerts:
            return 0.0
        
        approved_count = sum(1 for a in all_alerts if a.review_decision == "approved")
        
        return (approved_count / len(all_alerts)) * 100
    
    @staticmethod
    def get_false_positive_rate(session: Session) -> float:
        """
        Calculate rate of rejected alerts.
        
        Args:
            session: Database session
        
        Returns:
            False positive rate (0-100)
        """
        all_alerts = session.query(FraudAlert).all()
        
        if not all_alerts:
            return 0.0
        
        rejected_count = sum(1 for a in all_alerts if a.review_decision == "rejected")
        
        return (rejected_count / len(all_alerts)) * 100
    
    @staticmethod
    def get_customer_risk_profile(
        session: Session,
        customer_id: int
    ) -> Dict[str, Any]:
        """
        Get customer-specific risk profile.
        
        Args:
            session: Database session
            customer_id: Customer ID
        
        Returns:
            Dictionary with customer risk metrics
        """
        customer = session.query(Customer).filter(
            Customer.id == customer_id
        ).first()
        
        if not customer:
            return {}
        
        transactions = session.query(Transaction).filter(
            Transaction.customer_id == customer_id
        ).options(selectinload(Transaction.fraud_assessments)).all()
        
        total_transactions = len(transactions)
        
        high_risk_count = 0
        for txn in transactions:
            assessment = txn.fraud_assessments[0] if txn.fraud_assessments else None
            
            if assessment and assessment.risk_category.upper() == "HIGH":
                high_risk_count += 1
        
        fraud_rate = (high_risk_count / total_transactions * 100) if total_transactions > 0 else 0
        
        avg_transaction_amount = Decimal("0")
        if transactions:
            total_amount = sum(t.amount for t in transactions)
            avg_transaction_amount = total_amount / len(transactions)
        
        # Get suspicious patterns
        suspicious_patterns = AnalyticsService._detect_customer_patterns(
            session, customer_id
        )
        
        return {
            "customer_id": customer.customer_id,
            "total_transactions": total_transactions,
            "high_risk_count": high_risk_count,
            "fraud_rate": fraud_rate,
            "average_transaction_amount": float(avg_transaction_amount),
            "suspicious_patterns": suspicious_patterns,
            "risk_profile": customer.risk_profile,
        }
    
    @staticmethod
    def _detect_customer_patterns(
        session: Session,
        customer_id: int
    ) -> List[str]:
        """
        Detect suspicious patterns for a customer.
        
        Args:
            session: Database session
            customer_id: Customer ID
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Get last 30 days of transactions
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        transactions = session.query(Transaction).filter(
            and_(
                Transaction.customer_id == customer_id,
                Transaction.transaction_date >= cutoff_date
            )
        ).order_by(Transaction.transaction_date).all()
        
        if not transactions:
            return patterns
        
        # Check for velocity anomalies
        if len(transactions) > 10:
            patterns.append("High transaction frequency")
        
        # Check for large transaction spikes
        amounts = [t.amount for t in transactions]
        avg_amount = sum(amounts) / len(amounts) if amounts else Decimal("0")
        
        for amount in amounts:
            if amount > avg_amount * 3:
                patterns.append("Large transaction spike detected")
                break
        
        # Check for unusual transaction patterns
        if len(transactions) > 5:
            recent_transactions = transactions[-5:]
            recent_amounts = [t.amount for t in recent_transactions]
            
            if all(a > avg_amount for a in recent_amounts):
                patterns.append("Sustained elevated transaction amounts")
        
        return patterns
    
    @staticmethod
    def get_high_risk_customers(
        session: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top customers by fraud rate.
        
        Args:
            session: Database session
            limit: Number of customers to return
        
        Returns:
            List of high-risk customers with metrics
        """
        customers = session.query(Customer).all()
        
        customer_fraud_rates = []
        
        for customer in customers:
            profile = AnalyticsService.get_customer_risk_profile(session, customer.id)
            if profile:
                customer_fraud_rates.append(profile)
        
        # Sort by fraud rate descending
        customer_fraud_rates.sort(key=lambda x: x.get("fraud_rate", 0), reverse=True)
        
        return customer_fraud_rates[:limit]
    
    @staticmethod
    def get_geographic_risk_distribution(session: Session) -> Dict[str, Any]:
        """
        Get risk distribution by geographic location.
        
        Args:
            session: Database session
        
        Returns:
            Dictionary with geographic risk distribution
        """
        customers = session.query(Customer).all()
        
        geographic_data = {}
        
        for customer in customers:
            location = customer.country or "Unknown"
            
            if location not in geographic_data:
                geographic_data[location] = {
                    "total_customers": 0,
                    "total_transactions": 0,
                    "high_risk_count": 0,
                    "fraud_rate": 0.0,
                }
            
            geographic_data[location]["total_customers"] += 1
            
            # Count transactions for this customer
            transactions = session.query(Transaction).filter(
                Transaction.customer_id == customer.id
            ).all()
            
            geographic_data[location]["total_transactions"] += len(transactions)
            
            # Count high-risk transactions
            for txn in transactions:
                assessment = session.query(FraudAssessment).filter(
                    FraudAssessment.transaction_id == txn.id
                ).first()
                
                if assessment and assessment.risk_category.upper() == "HIGH":
                    geographic_data[location]["high_risk_count"] += 1
        
        # Calculate fraud rates
        for location in geographic_data:
            total = geographic_data[location]["total_transactions"]
            high_risk = geographic_data[location]["high_risk_count"]
            geographic_data[location]["fraud_rate"] = (high_risk / total * 100) if total > 0 else 0
        
        return geographic_data
    
    @staticmethod
    def detect_transaction_anomalies(
        session: Session,
        hours_lookback: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual transaction patterns.
        
        Args:
            session: Database session
            hours_lookback: Hours to analyze
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        cutoff_date = datetime.utcnow() - timedelta(hours=hours_lookback)
        
        # Get all transactions in the period
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        if not transactions:
            return anomalies
        
        # Detect volume spikes
        anomalies.extend(
            AnalyticsService._detect_volume_anomalies(session, transactions)
        )
        
        # Detect velocity anomalies
        anomalies.extend(
            AnalyticsService._detect_velocity_anomalies(transactions)
        )
        
        # Detect large transactions
        anomalies.extend(
            AnalyticsService._detect_large_transaction_anomalies(transactions)
        )
        
        return anomalies
    
    @staticmethod
    def _detect_volume_anomalies(
        session: Session,
        recent_transactions: List[Transaction]
    ) -> List[Dict[str, Any]]:
        """Detect volume spike anomalies."""
        anomalies = []
        
        # Get historical average
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        historical_transactions = session.query(Transaction).filter(
            Transaction.transaction_date < cutoff_date
        ).all()
        
        if not historical_transactions:
            return anomalies
        
        historical_count = len(historical_transactions)
        historical_avg_per_day = historical_count / 30
        
        current_count = len(recent_transactions)
        current_avg_per_day = current_count / 1  # Last 24 hours
        
        if current_avg_per_day > historical_avg_per_day * AnalyticsService.ANOMALY_THRESHOLDS["volume_spike"]:
            anomalies.append({
                "type": "volume_spike",
                "severity": "high",
                "description": f"Transaction volume {current_avg_per_day:.0f} is {(current_avg_per_day/historical_avg_per_day):.1f}x historical average",
                "current_volume": current_count,
                "expected_volume": int(historical_avg_per_day),
            })
        
        return anomalies
    
    @staticmethod
    def _detect_velocity_anomalies(
        transactions: List[Transaction]
    ) -> List[Dict[str, Any]]:
        """Detect velocity anomalies (multiple transactions rapidly)."""
        anomalies = []
        
        # Group by customer
        customer_txns = {}
        for txn in transactions:
            if txn.customer_id not in customer_txns:
                customer_txns[txn.customer_id] = []
            customer_txns[txn.customer_id].append(txn)
        
        # Check for rapid transactions per customer
        for customer_id, txns in customer_txns.items():
            if len(txns) >= AnalyticsService.ANOMALY_THRESHOLDS["velocity_threshold"]:
                # Sort by timestamp
                txns_sorted = sorted(txns, key=lambda x: x.transaction_date)
                
                # Check if within 1 hour
                time_span = txns_sorted[-1].transaction_date - txns_sorted[0].transaction_date
                
                if time_span.total_seconds() < 3600:
                    anomalies.append({
                        "type": "velocity_anomaly",
                        "severity": "high",
                        "description": f"Customer {customer_id} made {len(txns)} transactions in {time_span.total_seconds():.0f} seconds",
                        "customer_id": customer_id,
                        "transaction_count": len(txns),
                        "time_span_seconds": time_span.total_seconds(),
                    })
        
        return anomalies
    
    @staticmethod
    def _detect_large_transaction_anomalies(
        transactions: List[Transaction]
    ) -> List[Dict[str, Any]]:
        """Detect unusually large transactions."""
        anomalies = []
        
        threshold = Decimal(str(AnalyticsService.ANOMALY_THRESHOLDS["large_transaction"]))
        
        large_txns = [t for t in transactions if t.amount > threshold]
        
        if large_txns:
            for txn in large_txns:
                anomalies.append({
                    "type": "large_transaction",
                    "severity": "medium",
                    "description": f"Transaction amount {float(txn.amount)} exceeds threshold {float(threshold)}",
                    "transaction_id": txn.transaction_id,
                    "amount": float(txn.amount),
                    "customer_id": txn.customer_id,
                })
        
        return anomalies
    
    @staticmethod
    def score_transaction_anomaly(
        session: Session,
        transaction_id: int
    ) -> float:
        """
        Score how anomalous a transaction is (0-100).
        
        Args:
            session: Database session
            transaction_id: Transaction ID
        
        Returns:
            Anomaly score (0-100)
        """
        transaction = session.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return 0.0
        
        anomaly_score = 0.0
        
        # Get customer's average transaction amount
        customer_txns = session.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id
        ).all()
        
        if customer_txns:
            avg_amount = sum(t.amount for t in customer_txns) / len(customer_txns)
            
            # Score based on deviation from average
            if transaction.amount > avg_amount:
                deviation_ratio = float(transaction.amount / avg_amount)
                anomaly_score += min(50, (deviation_ratio - 1) * 25)
        
        # Check for velocity anomalies
        cutoff_time = transaction.transaction_date - timedelta(hours=1)
        recent_txns = session.query(Transaction).filter(
            and_(
                Transaction.customer_id == transaction.customer_id,
                Transaction.transaction_date >= cutoff_time,
                Transaction.transaction_date <= transaction.transaction_date
            )
        ).all()
        
        if len(recent_txns) > 5:
            anomaly_score += min(50, len(recent_txns) * 5)
        
        return min(100.0, anomaly_score)
    
    @staticmethod
    def get_dashboard_overview(session: Session) -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview metrics.
        
        Args:
            session: Database session
        
        Returns:
            Dictionary with dashboard metrics
        """
        # Get 30-day statistics
        txn_stats = AnalyticsService.get_transaction_statistics(session, days=30)
        alert_stats = AnalyticsService.get_alert_statistics(session, days=30)
        risk_dist = AnalyticsService.get_risk_distribution(session, days=30)
        high_risk_customers = AnalyticsService.get_high_risk_customers(session, limit=5)
        
        fraud_rate = AnalyticsService.get_fraud_confirmed_rate(session)
        false_positive_rate = AnalyticsService.get_false_positive_rate(session)
        
        # Detect recent anomalies
        anomalies = AnalyticsService.detect_transaction_anomalies(session, hours_lookback=24)
        critical_anomalies = sum(1 for a in anomalies if a.get("severity") == "high")
        
        return {
            "total_transactions": txn_stats["total_transactions"],
            "total_alerts": alert_stats["total_alerts"],
            "fraud_confirmation_rate": fraud_rate,
            "false_positive_rate": false_positive_rate,
            "approval_rate": alert_stats["approval_rate"],
            "rejection_rate": alert_stats["rejection_rate"],
            "average_review_time_hours": alert_stats["average_review_time_hours"],
            "high_risk_customers_count": len(high_risk_customers),
            "critical_anomalies": critical_anomalies,
            "pending_alerts": alert_stats["pending_alerts"],
            "under_review_alerts": alert_stats["under_review_alerts"],
            "risk_distribution": risk_dist,
        }

    @staticmethod
    def get_merchant_category_analysis(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get transaction volume and risk by merchant category."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        category_data = {}
        for txn in transactions:
            category = txn.merchant_category or "Unknown"
            if category not in category_data:
                category_data[category] = {
                    "category": category,
                    "transaction_count": 0,
                    "total_volume": Decimal("0"),
                    "high_risk_count": 0,
                    "total_risk_score": 0,
                }
            
            category_data[category]["transaction_count"] += 1
            category_data[category]["total_volume"] += txn.amount
            
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.transaction_id == txn.id
            ).first()
            if assessment:
                category_data[category]["total_risk_score"] += assessment.risk_score
                if assessment.risk_category.upper() == "HIGH":
                    category_data[category]["high_risk_count"] += 1
        
        result = []
        for cat_data in category_data.values():
            count = cat_data["transaction_count"]
            avg_risk = cat_data["total_risk_score"] / count if count > 0 else 0
            result.append({
                "category": cat_data["category"],
                "transaction_count": count,
                "total_volume": float(cat_data["total_volume"]),
                "average_risk_score": avg_risk,
            })
        
        return sorted(result, key=lambda x: x["transaction_count"], reverse=True)

    @staticmethod
    def get_transaction_type_analysis(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get transaction breakdown by type."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        type_data = {}
        for txn in transactions:
            txn_type = txn.transaction_type or "unknown"
            if txn_type not in type_data:
                type_data[txn_type] = {
                    "transaction_type": txn_type,
                    "count": 0,
                    "volume": Decimal("0"),
                    "high_risk_count": 0,
                    "total_risk_score": 0,
                }
            
            type_data[txn_type]["count"] += 1
            type_data[txn_type]["volume"] += txn.amount
            
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.transaction_id == txn.id
            ).first()
            if assessment:
                type_data[txn_type]["total_risk_score"] += assessment.risk_score
                if assessment.risk_category.upper() == "HIGH":
                    type_data[txn_type]["high_risk_count"] += 1
        
        result = []
        for t_data in type_data.values():
            count = t_data["count"]
            avg_risk = t_data["total_risk_score"] / count if count > 0 else 0
            result.append({
                "transaction_type": t_data["transaction_type"],
                "count": count,
                "volume": float(t_data["volume"]),
                "high_risk_count": t_data["high_risk_count"],
                "average_risk_score": avg_risk,
            })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)

    @staticmethod
    def get_payment_method_analysis(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get payment method distribution and fraud rates."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        method_data = {}
        for txn in transactions:
            method = txn.payment_method or "unknown"
            if method not in method_data:
                method_data[method] = {
                    "payment_method": method,
                    "count": 0,
                    "volume": Decimal("0"),
                    "high_risk_count": 0,
                }
            
            method_data[method]["count"] += 1
            method_data[method]["volume"] += txn.amount
            
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.transaction_id == txn.id
            ).first()
            if assessment and assessment.risk_category.upper() == "HIGH":
                method_data[method]["high_risk_count"] += 1
        
        result = []
        for m_data in method_data.values():
            count = m_data["count"]
            high_risk = m_data["high_risk_count"]
            fraud_rate = (high_risk / count * 100) if count > 0 else 0
            result.append({
                "payment_method": m_data["payment_method"],
                "count": count,
                "volume": float(m_data["volume"]),
                "high_risk_count": high_risk,
                "fraud_rate": fraud_rate,
            })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)

    @staticmethod
    def get_geographic_analysis(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get transaction data by geographic location."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        geo_data = {}
        for txn in transactions:
            country = txn.location_country or "Unknown"
            city = txn.location_city or "Unknown"
            key = f"{country}|{city}"
            
            if key not in geo_data:
                geo_data[key] = {
                    "country": country,
                    "city": city,
                    "transaction_count": 0,
                    "total_volume": Decimal("0"),
                    "high_risk_count": 0,
                    "total_risk_score": 0,
                }
            
            geo_data[key]["transaction_count"] += 1
            geo_data[key]["total_volume"] += txn.amount
            
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.transaction_id == txn.id
            ).first()
            if assessment:
                geo_data[key]["total_risk_score"] += assessment.risk_score
                if assessment.risk_category.upper() == "HIGH":
                    geo_data[key]["high_risk_count"] += 1
        
        result = []
        for g_data in geo_data.values():
            count = g_data["transaction_count"]
            avg_risk = g_data["total_risk_score"] / count if count > 0 else 0
            result.append({
                "country": g_data["country"],
                "city": g_data["city"],
                "transaction_count": count,
                "total_volume": float(g_data["total_volume"]),
                "high_risk_count": g_data["high_risk_count"],
                "average_risk_score": avg_risk,
            })
        
        return sorted(result, key=lambda x: x["transaction_count"], reverse=True)

    @staticmethod
    def get_channel_analysis(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get transaction volume and fraud by channel."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        transactions = session.query(Transaction).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        channel_data = {}
        for txn in transactions:
            channel = txn.channel or "unknown"
            if channel not in channel_data:
                channel_data[channel] = {
                    "channel": channel,
                    "count": 0,
                    "volume": Decimal("0"),
                    "high_risk_count": 0,
                }
            
            channel_data[channel]["count"] += 1
            channel_data[channel]["volume"] += txn.amount
            
            assessment = session.query(FraudAssessment).filter(
                FraudAssessment.transaction_id == txn.id
            ).first()
            if assessment and assessment.risk_category.upper() == "HIGH":
                channel_data[channel]["high_risk_count"] += 1
        
        result = []
        for c_data in channel_data.values():
            count = c_data["count"]
            high_risk = c_data["high_risk_count"]
            fraud_rate = (high_risk / count * 100) if count > 0 else 0
            result.append({
                "channel": c_data["channel"],
                "count": count,
                "volume": float(c_data["volume"]),
                "high_risk_count": high_risk,
                "fraud_rate": fraud_rate,
            })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)

    @staticmethod
    def get_risk_score_distribution(
        session: Session,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get risk score distribution histogram data."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        assessments = session.query(FraudAssessment).join(
            Transaction
        ).filter(
            Transaction.transaction_date >= cutoff_date
        ).all()
        
        # Create buckets: 0-10, 10-20, ..., 90-100
        buckets = {
            "0-10": 0,
            "10-20": 0,
            "20-30": 0,
            "30-40": 0,
            "40-50": 0,
            "50-60": 0,
            "60-70": 0,
            "70-80": 0,
            "80-90": 0,
            "90-100": 0,
        }
        
        for assessment in assessments:
            score = int(assessment.risk_score)
            bucket_idx = min(score // 10, 9)
            bucket_key = f"{bucket_idx * 10}-{(bucket_idx + 1) * 10}"
            if bucket_key in buckets:
                buckets[bucket_key] += 1
        
        total = sum(buckets.values())
        result = []
        for bucket_name, count in buckets.items():
            percentage = (count / total * 100) if total > 0 else 0
            result.append({
                "risk_score_bucket": bucket_name,
                "count": count,
                "percentage": percentage,
            })
        
        return result
