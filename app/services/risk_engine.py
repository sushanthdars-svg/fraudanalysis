"""
Risk Engine Service - Combines fraud rule scores and ML predictions for risk assessment.
Implements comprehensive risk scoring logic with rule-based and ML-based detection.
"""

import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAssessment, TriggeredRule
from app.models.fraud_rule import FraudRule
from app.services.fraud_engine import FraudEngine
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Comprehensive risk scoring engine that combines fraud rules and ML predictions.
    
    Risk Scoring Formula:
    - Rule Score: Sum of triggered rule severities (0-100)
    - ML Score: Average of model predictions (0-1, converted to 0-100)
    - Combined Score: 0.60 * Rule Score + 0.40 * ML Score
    
    Risk Levels:
    - LOW: 0-30
    - MEDIUM: 31-70
    - HIGH: 71-100
    """
    
    # Scoring configuration
    RULE_WEIGHT = 0.60
    ML_WEIGHT = 0.40
    
    # Risk level thresholds
    RISK_LEVELS = {
        "LOW": (0, 30),
        "MEDIUM": (31, 70),
        "HIGH": (71, 100),
    }
    
    # Alert thresholds
    ALERT_THRESHOLD_MIN = 31  # MEDIUM or higher
    
    # Severity weights for rules
    SEVERITY_WEIGHTS = {
        "low": Decimal("10"),
        "medium": Decimal("20"),
        "high": Decimal("30"),
        "critical": Decimal("50"),
    }
    
    def __init__(self):
        """Initialize risk engine with fraud engine and ML service."""
        self.fraud_engine = FraudEngine()
        self.ml_service = MLService()
    
    def assess_fraud_risk(
        self,
        session: Session,
        transaction_id: int,
        customer_id: Optional[int] = None,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess fraud risk for a transaction by combining rules and ML predictions.
        
        Args:
            session: Database session
            transaction_id: Transaction ID (database primary key)
            customer_id: Customer ID (optional, looked up if not provided)
            transaction_data: Pre-loaded transaction data (optional)
        
        Returns:
            Dictionary containing:
            - assessment_id: Unique assessment ID (primary key)
            - transaction_id: Transaction ID
            - risk_score: Final risk score (0-100)
            - risk_level: Risk category (LOW/MEDIUM/HIGH)
            - rule_score: Rule-based score (0-100)
            - ml_score: ML-based score (0-100)
            - triggered_rules: List of triggered rule details
            - alert_required: Whether alert should be created
            - created_at: Assessment timestamp
        
        Raises:
            ValueError: If transaction not found
        """
        try:
            # Load transaction if not provided
            if transaction_data is None:
                transaction = session.query(Transaction).filter(
                    Transaction.id == transaction_id
                ).first()
                
                if not transaction:
                    raise ValueError(f"Transaction {transaction_id} not found")
                
                transaction_data = self._prepare_transaction_data(transaction)
                customer_id = transaction.customer_id
            
            logger.info(f"Assessing fraud risk for transaction {transaction_id}")
            
            # Execute fraud rules using evaluate_transaction
            # This returns (risk_score, risk_level, triggered_rules)
            transaction = session.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            rule_score_result, rule_level, triggered_rules = self.fraud_engine.evaluate_transaction(
                db=session,
                transaction=transaction
            )
            
            # Convert rule_score to 0-100 range if it's in decimal format
            rule_score = float(rule_score_result)
            
            logger.debug(f"Rule score: {rule_score}, Triggered: {len(triggered_rules)}")
            
            # Get ML predictions
            ml_score = self._get_ml_score(session, transaction_data)
            logger.debug(f"ML score: {ml_score}")
            
            # Calculate combined risk score
            combined_score = self._calculate_combined_score(rule_score, ml_score)
            
            # Determine risk level
            risk_level = self.calculate_risk_level(combined_score)
            
            # Determine if alert should be created
            alert_required = self.should_create_alert(combined_score, risk_level)
            
            # Create assessment record
            assessment = FraudAssessment(
                transaction_id=transaction_id,
                risk_score=Decimal(str(round(combined_score, 2))),
                risk_category=risk_level,
                rules_triggered_count=len(triggered_rules),
                ml_score=Decimal(str(round(ml_score / 100.0, 4))) if ml_score > 0 else None,
                ml_model_version="1.0",
                engine_version="1.0",
                assessment_timestamp=datetime.utcnow(),
                explanation=self._generate_explanation(
                    combined_score, rule_score, ml_score, risk_level, triggered_rules
                ),
                assessment_metadata={
                    "rule_weight": float(self.RULE_WEIGHT),
                    "ml_weight": float(self.ML_WEIGHT),
                    "triggered_rule_count": len(triggered_rules),
                    "assessment_version": "1.0",
                }
            )
            
            session.add(assessment)
            session.flush()  # Flush to get assessment ID
            
            # Record triggered rules
            for rule in triggered_rules:
                # Handle both dict and RuleResult object
                rule_id = rule.get("rule_id") if isinstance(rule, dict) else rule.rule_id
                rule_explanation = rule.get("explanation", "") if isinstance(rule, dict) else rule.explanation
                
                triggered_rule = TriggeredRule(
                    assessment_id=assessment.id,
                    transaction_id=transaction_id,
                    rule_id=rule_id,
                    trigger_timestamp=datetime.utcnow(),
                    rule_explanation=rule_explanation,
                    triggered_values={}
                )
                session.add(triggered_rule)
            
            session.commit()
            
            logger.info(
                f"Risk assessment complete: score={combined_score}, level={risk_level}, "
                f"rules={len(triggered_rules)}, alert_required={alert_required}"
            )
            
            return {
                "assessment_id": assessment.id,
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "risk_score": float(combined_score),
                "risk_level": risk_level,
                "rule_score": float(rule_score),
                "ml_score": float(ml_score),
                "triggered_rules": triggered_rules,
                "alert_required": alert_required,
                "created_at": assessment.assessment_timestamp,
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error assessing fraud risk: {e}", exc_info=True)
            raise
    
    def _prepare_transaction_data(self, transaction: Transaction) -> Dict[str, Any]:
        """Convert transaction model to data dictionary for processing."""
        return {
            "transaction_id": transaction.transaction_id,
            "customer_id": transaction.customer_id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "merchant_name": transaction.merchant_name,
            "merchant_id": transaction.merchant_id,
            "merchant_category": transaction.merchant_category,
            "transaction_type": transaction.transaction_type,
            "payment_method": transaction.payment_method,
            "transaction_date": transaction.transaction_date,
            "country": transaction.location_country,
            "city": transaction.location_city,
            "status": transaction.status,
        }
    
    def _calculate_rule_score(self, rule_results: Dict[str, Any]) -> Tuple[float, List[Dict]]:
        """
        Calculate rule-based score from triggered rules.
        
        Args:
            rule_results: Dict containing 'triggered_rules', 'rule_score' from FraudEngine
        
        Returns:
            Tuple of (rule_score: 0-100, triggered_rules: list of rule details)
        """
        triggered_rules = []
        
        # Extract triggered_rules list from the results dict
        rules_list = rule_results.get("triggered_rules", [])
        
        # If FraudEngine already calculated the rule_score, use it
        if "rule_score" in rule_results:
            rule_score = min(float(rule_results["rule_score"]), 100.0)
        else:
            # Otherwise, calculate from triggered rules
            rule_score = Decimal("0")
            for result in rules_list:
                severity = result.get("severity", "low").lower()
                weight = self.SEVERITY_WEIGHTS.get(severity, Decimal("10"))
                rule_score += weight
            
            # Cap at 100
            rule_score = min(float(rule_score), 100.0)
        
        # Extract triggered rule details for reporting
        for result in rules_list:
            triggered_rules.append({
                "rule_id": result.get("rule_id"),
                "name": result.get("name"),
                "severity": result.get("severity", "low").lower(),
                "explanation": result.get("explanation", ""),
                "triggered_values": result.get("triggered_values", {}),
            })
        
        return float(rule_score), triggered_rules
    
    def _get_ml_score(self, session: Session, transaction_data: Dict[str, Any]) -> float:
        """
        Get ML-based fraud prediction score (0-100).
        
        Handles missing models gracefully by returning 0.
        Accepts ml_score (0-100) or fraud_probability (0-1).
        """
        try:
            # Try to get ML predictions
            ml_prediction = self.ml_service.predict_fraud(
                session=session,
                transaction_data=transaction_data
            )
            
            if ml_prediction is None:
                logger.warning("ML service returned None, using score 0")
                return 0.0
            
            # Check for pre-computed ml_score (0-100)
            if "ml_score" in ml_prediction:
                score = float(ml_prediction.get("ml_score", 0.0))
                return min(max(score, 0.0), 100.0)  # Clamp to [0, 100]
            
            # Check for fraud_probability (0-1) and convert to score
            if "fraud_probability" in ml_prediction:
                score = ml_prediction.get("fraud_probability", 0.0) * 100.0
                return min(max(score, 0.0), 100.0)  # Clamp to [0, 100]
            
            # Check for probability field (0-1) and convert to score
            if "probability" in ml_prediction:
                score = ml_prediction.get("probability", 0.0) * 100.0
                return min(max(score, 0.0), 100.0)  # Clamp to [0, 100]
            
            # Default to 0 if no recognized score field
            logger.warning(f"ML prediction missing expected score field: {ml_prediction.keys()}")
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error getting ML score, using 0: {e}")
            return 0.0
    
    def _calculate_combined_score(self, rule_score: float, ml_score: float) -> float:
        """
        Calculate combined risk score using weighted average.
        Formula: 0.60 * rule_score + 0.40 * ml_score
        """
        combined = (rule_score * self.RULE_WEIGHT) + (ml_score * self.ML_WEIGHT)
        return min(max(combined, 0.0), 100.0)  # Clamp to [0, 100]
    
    def calculate_risk_level(self, score: float) -> str:
        """
        Categorize risk score into risk level.
        
        Args:
            score: Risk score (0-100)
        
        Returns:
            Risk level: "LOW", "MEDIUM", or "HIGH"
        """
        if score <= 30:
            return "LOW"
        elif score <= 70:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def should_create_alert(self, risk_score: float, risk_level: str) -> bool:
        """
        Determine if an alert should be created.
        
        Creates alerts for MEDIUM (31-70) and HIGH (71-100) risk transactions.
        """
        return risk_score >= self.ALERT_THRESHOLD_MIN
    
    def _generate_explanation(
        self,
        combined_score: float,
        rule_score: float,
        ml_score: float,
        risk_level: str,
        triggered_rules: List[Dict]
    ) -> str:
        """Generate human-readable explanation of risk assessment."""
        explanation_parts = [
            f"Risk Assessment Results:",
            f"- Combined Risk Score: {combined_score:.2f}/100 ({risk_level})",
            f"- Rule-Based Score: {rule_score:.2f}/100 ({self.RULE_WEIGHT*100:.0f}% weight)",
            f"- ML-Based Score: {ml_score:.2f}/100 ({self.ML_WEIGHT*100:.0f}% weight)",
        ]
        
        if triggered_rules:
            explanation_parts.append(f"- Triggered Rules ({len(triggered_rules)}):")
            for rule in triggered_rules:
                # RuleResult objects have attributes, not dict keys
                rule_name = rule.rule_name if hasattr(rule, 'rule_name') else rule.get('name', 'Unknown')
                rule_id = rule.rule_id if hasattr(rule, 'rule_id') else rule.get('rule_id', 'Unknown')
                explanation = rule.explanation if hasattr(rule, 'explanation') else rule.get('explanation', '')
                explanation_parts.append(
                    f"  • {rule_name} ({rule_id}): {explanation}"
                )
        else:
            explanation_parts.append("- No fraud rules triggered")
        
        if ml_score > 0:
            explanation_parts.append(f"- ML Models: Fraud probability detected")
        
        return "\n".join(explanation_parts)
    
    def get_assessment(self, session: Session, assessment_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a fraud assessment by ID.
        
        Args:
            session: Database session
            assessment_id: Assessment ID
        
        Returns:
            Assessment details or None if not found
        """
        assessment = session.query(FraudAssessment).filter(
            FraudAssessment.id == assessment_id
        ).first()
        
        if not assessment:
            return None
        
        # Get triggered rules
        triggered_rules = session.query(TriggeredRule).filter(
            TriggeredRule.assessment_id == assessment_id
        ).all()
        
        return {
            "assessment_id": assessment.id,
            "transaction_id": assessment.transaction_id,
            "risk_score": float(assessment.risk_score),
            "risk_category": assessment.risk_category,
            "rules_triggered_count": assessment.rules_triggered_count,
            "ml_score": float(assessment.ml_score) if assessment.ml_score else None,
            "ml_model_version": assessment.ml_model_version,
            "engine_version": assessment.engine_version,
            "assessment_timestamp": assessment.assessment_timestamp,
            "explanation": assessment.explanation,
            "assessment_metadata": assessment.assessment_metadata,
            "triggered_rules": [
                {
                    "rule_id": tr.rule_id,
                    "rule_explanation": tr.rule_explanation,
                    "trigger_timestamp": tr.trigger_timestamp,
                    "triggered_values": tr.triggered_values,
                }
                for tr in triggered_rules
            ],
        }
    
    def get_transaction_assessment(
        self,
        session: Session,
        transaction_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve assessment for a specific transaction.
        
        Args:
            session: Database session
            transaction_id: Transaction database ID
        
        Returns:
            Assessment details or None if not found
        """
        assessment = session.query(FraudAssessment).filter(
            FraudAssessment.transaction_id == transaction_id
        ).first()
        
        if not assessment:
            return None
        
        return self.get_assessment(session, assessment.id)
