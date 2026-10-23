#!/usr/bin/env python
"""Mock backend API server to support frontend development.

This bypasses the SQLAlchemy DLL loading issue by providing
a minimal FastAPI server with mock authentication endpoints.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import json
import re
from datetime import datetime, timedelta
import jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Secret key for JWT
SECRET_KEY = "dev_secret_key_change_in_production_minimum_32_chars_required"
ALGORITHM = "HS256"

# Password validation function
def validate_email_format(email: str) -> bool:
    """Validate email format - supports .local domains for development."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*etc.)"
    return True, ""

# Create FastAPI application
app = FastAPI(
    title="Financial Risk Analysis and Hybrid Fraud Detection System (Mock)",
    description="Development mock backend for frontend testing",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class LoginRequest(BaseModel):
    email: str = Field(..., description="Email address (supports .local domains)")
    password: str

class RegistrationRequest(BaseModel):
    email: str = Field(..., description="Email address (supports .local domains)")
    password: str
    full_name: str = ""

class GoogleLoginRequest(BaseModel):
    email: str = Field(..., description="Email address (supports .local domains)")
    full_name: str = ""
    token: str = ""

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

class UpdateRuleRequest(BaseModel):
    is_enabled: bool = None
    name: str = None
    description: str = None
    threshold_value: int = None
    risk_weight: int = None
    severity: str = None

class UpdateUserRequest(BaseModel):
    is_active: bool = None
    role: str = None

class CreateTeamMemberRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "viewer"

class CreateTeamMemberRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "viewer"

# Mock data store
MOCK_USERS = {
    "admin@fraud-detection.local": {
        "id": 1,
        "email": "admin@fraud-detection.local",
        "password": "password",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    },
    "analyst@fraud-detection.local": {
        "id": 2,
        "email": "analyst@fraud-detection.local",
        "password": "password",
        "full_name": "Risk Analyst",
        "role": "analyst",
        "is_active": True
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": "development",
        "version": "1.0.0",
        "mode": "mock"
    }

@app.post("/backend/api/auth/login")
@app.post("/api/auth/login")
async def login(email: str, password: str) -> LoginResponse:
    """
    Login endpoint - mock version.
    
    Default test credentials:
    - Email: admin@fraud-detection.local
    - Password: password
    
    - Email: analyst@fraud-detection.local
    - Password: password
    """
    email = email.lower()
    
    # Find user
    user = MOCK_USERS.get(email)
    if not user or user["password"] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Create token
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"]
        }
    )

@app.post("/backend/api/auth/register")
@app.post("/api/auth/register")
async def register(email: str, password: str, full_name: str = ""):
    """Register endpoint - mock version with password strength validation."""
    email = email.lower()
    
    if email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )
    
    # Create new user and persist
    user_id = max(u["id"] for u in MOCK_USERS.values()) + 1 if MOCK_USERS else 3
    name = full_name.strip() if full_name else email.split("@")[0].title()
    
    new_user = {
        "id": user_id,
        "email": email,
        "password": password,
        "full_name": name,
        "role": "viewer",
        "is_active": True
    }
    MOCK_USERS[email] = new_user
    logger.info(f"Registered new user: {email}")
    
    # Create token
    access_token = create_access_token(
        data={"sub": new_user["email"], "role": new_user["role"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": new_user["id"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "role": new_user["role"],
            "is_active": new_user["is_active"]
        }
    ).model_dump()

@app.post("/backend/api/auth/google")
@app.post("/api/auth/google")
async def google_login(email: str, full_name: str = "", token: str = ""):
    """Google login endpoint - mock version."""
    email = email.lower()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email required for Google login",
        )
    
    # Check if user exists, if not create one
    if email not in MOCK_USERS:
        user_id = max(u["id"] for u in MOCK_USERS.values()) + 1 if MOCK_USERS else 3
        new_user = {
            "id": user_id,
            "email": email,
            "password": "google_oauth",
            "full_name": full_name or email.split("@")[0].title(),
            "role": "viewer",
            "is_active": True
        }
        MOCK_USERS[email] = new_user
        logger.info(f"Created new user via Google login: {email}")
    
    user = MOCK_USERS[email]
    
    # Create token
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"]
        }
    )

@app.get("/backend/api/auth/me")
@app.get("/api/auth/me")
async def get_current_user():
    """Get current user endpoint."""
    return {
        "id": 1,
        "email": "admin@fraud-detection.local",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    }


@app.get("/backend/api/dashboard/overview")
@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data."""
    return {
        "total_transactions": 1_000_000,
        "flagged_transactions": 125,
        "fraud_detected": 42,
        "high_risk_alerts": 8,
        "medium_risk_alerts": 23,
        "low_risk_alerts": 45,
        "ml_accuracy": 0.964,
        "false_positive_rate": 0.023,
        "avg_response_time_ms": 145,
        "system_status": "operational"
    }

@app.get("/backend/api/alerts")
@app.get("/api/alerts")
async def get_alerts(skip: int = 0, limit: int = 10):
    """Get fraud alerts."""
    statuses = ["new", "reviewing", "resolved", "dismissed"]
    alerts = [
        {
            "id": i,
            "transaction_id": 1000 + i,
            "risk_level": ["high", "medium", "low"][i % 3],
            "description": f"Potential fraud detected in transaction {1000 + i}",
            "status": statuses[i % len(statuses)],
            "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "updated_at": (datetime.utcnow() - timedelta(hours=i//2)).isoformat()
        }
        for i in range(1, limit + 1)
    ]
    return {
        "total": 156,
        "alerts": alerts,
        "skip": skip,
        "limit": limit
    }

@app.get("/backend/api/models")
@app.get("/api/models")
async def get_models():
    """Get ML models list including trained models."""
    default_models = [
        {
            "id": "default_1",
            "name": "gradient_boosting",
            "version": "2.1.0",
            "training_date": "2024-01-15T00:00:00",
            "data_source": "database",
            "dataset_size": 50000,
            "total_samples": 100000,
            "evaluation_only": False,
            "feature_names": ["velocity_score", "amount_zscore", "device_entropy", "ip_reputation", "account_age_days", "auth_fail_count", "timezone_delta", "merchant_category_shift"],
            "metrics": {
                "accuracy": 0.972,
                "precision": 0.95,
                "recall": 0.91,
                "f1_score": 0.93,
                "roc_auc": 0.978,
                "confusion_matrix": {"true_positive": 910, "false_positive": 47, "true_negative": 19950, "false_negative": 93}
            },
            "cv_mean": 0.91,
            "feature_importance": [0.28, 0.22, 0.18, 0.15, 0.10, 0.04, 0.02, 0.01]
        },
        {
            "id": "default_2",
            "name": "random_forest",
            "version": "1.8.0",
            "training_date": "2023-11-20T00:00:00",
            "data_source": "database",
            "dataset_size": 45000,
            "total_samples": 90000,
            "evaluation_only": False,
            "feature_names": ["velocity_score", "amount_zscore", "device_entropy", "ip_reputation", "account_age_days", "auth_fail_count", "timezone_delta", "merchant_category_shift"],
            "metrics": {
                "accuracy": 0.948,
                "precision": 0.92,
                "recall": 0.87,
                "f1_score": 0.89,
                "roc_auc": 0.955,
                "confusion_matrix": {"true_positive": 870, "false_positive": 73, "true_negative": 19850, "false_negative": 207}
            },
            "cv_mean": 0.87,
            "feature_importance": [0.25, 0.20, 0.17, 0.14, 0.12, 0.06, 0.04, 0.02]
        }
    ]
    # Add trained models to the list
    all_models = default_models + list(TRAINED_MODELS.values())
    return {
        "items": all_models
    }

@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data."""
    return {
        "total_alerts": 156,
        "pending_alerts": 8,
        "under_review_alerts": 23,
        "high_risk_customers_count": 12,
        "fraud_confirmation_rate": 0.85,
        "false_positive_rate": 0.023,
        "system_status": "operational"
    }

@app.get("/api/analytics/transactions")
async def get_analytics_transactions(days: int = 30):
    """Get transaction analytics over time."""
    from datetime import timedelta
    transactions = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days-i)).strftime("%Y-%m-%d")
        transactions.append({
            "date": date,
            "transaction_count": 5000 + (i * 100),
            "total_volume": 500000 + (i * 10000)
        })
    
    total_trans = 150000 + (days * 5000)
    high_risk = int(total_trans * 0.08)
    medium_risk = int(total_trans * 0.15)
    low_risk = int(total_trans * 0.65)
    
    return {
        "total_transactions": total_trans,
        "total_volume": 15000000 + (days * 500000),
        "average_amount": 100.0,
        "high_risk_transactions": high_risk,
        "medium_risk_transactions": medium_risk,
        "low_risk_transactions": low_risk
    }

@app.get("/api/analytics/trends")
async def get_analytics_trends(days: int = 30):
    """Get risk trends over time."""
    from datetime import timedelta
    trends = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days-i)).strftime("%Y-%m-%d")
        trends.append({
            "date": date,
            "total_volume": 500000 + (i * 10000),
            "transaction_count": 5000 + (i * 100)
        })
    return trends

@app.get("/backend/api/transactions")
@app.get("/backend/api/transactions")
@app.get("/api/transactions")
async def get_transactions(page: int = 1, limit: int = 20):
    """Get paginated transactions."""
    from datetime import timedelta
    risk_levels = ["low", "medium", "high"]
    statuses = ["completed", "pending", "flagged"]
    
    total = 10000
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit
    
    transactions = [
        {
            "id": offset + i + 1,
            "transaction_id": f"TXN-{1000000 + offset + i}",
            "customer_id": 100000 + (offset + i) % 5000,
            "amount": 50 + ((offset + i) * 7.5 % 10000),
            "currency": "USD",
            "merchant_name": f"Merchant-{(offset + i) % 500}",
            "transaction_date": (datetime.utcnow() - timedelta(hours=(offset + i))).isoformat(),
            "risk_level": risk_levels[(offset + i) % 3],
            "status": statuses[(offset + i) % 3],
            "risk_score": round((offset + i) % 100 / 100.0, 2)
        }
        for i in range(limit)
    ]
    
    return {
        "data": transactions,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages
        }
    }

@app.get("/backend/api/transactions/{transaction_id}")
@app.get("/api/transactions/{transaction_id}")
async def get_transaction_detail(transaction_id: str):
    """Get transaction details."""
    from datetime import timedelta
    return {
        "id": transaction_id,
        "customer_id": "CUST-123456",
        "amount": 5432.10,
        "risk_level": "high",
        "status": "flagged",
        "timestamp": datetime.utcnow().isoformat(),
        "merchant": "Online Retailer Inc",
        "fraud_score": 0.92,
        "description": "High-risk international transaction detected",
        "ip_address": "192.168.1.100",
        "device_id": "DEV-ABC123",
        "location": "Singapore",
        "previous_transactions": 45,
        "velocity_score": 0.87
    }

@app.get("/api/audit-logs")
@app.get("/backend/api/audit-logs")
async def get_audit_logs(skip: int = 0, limit: int = 20, actor: str = None, action: str = None, start_date: str = None, end_date: str = None):
    """Get audit logs with optional filtering."""
    from datetime import date as date_type
    
    actions_list = ["login", "alert_resolved", "model_updated", "config_changed", "user_created", "role_updated", "rule_enabled", "rule_disabled", "user_deactivated"]
    statuses = ["success", "failed"]
    
    # Generate all audit items
    all_items = []
    total_available = 500
    
    for i in range(total_available):
        item_date = datetime.utcnow() - timedelta(hours=i)
        all_items.append({
            "id": i + 1,
            "timestamp": item_date.isoformat(),
            "actor": actor if actor else "admin@fraud-detection.local" if i % 3 == 0 else "analyst@fraud-detection.local",
            "action": actions_list[i % len(actions_list)],
            "target_type": "alert" if i % 3 == 0 else "user" if i % 3 == 1 else "model",
            "target_id": str(1000 + i),
            "status": statuses[i % 2],
            "details": f"Action performed on target {i + 1}"
        })
    
    # Apply filters
    filtered_items = all_items
    
    if actor:
        filtered_items = [item for item in filtered_items if actor.lower() in item["actor"].lower()]
    
    if action:
        filtered_items = [item for item in filtered_items if action.lower() in item["action"].lower()]
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date + "T00:00:00")
            filtered_items = [item for item in filtered_items if datetime.fromisoformat(item["timestamp"]) >= start_dt]
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date + "T23:59:59")
            filtered_items = [item for item in filtered_items if datetime.fromisoformat(item["timestamp"]) <= end_dt]
        except:
            pass
    
    total = len(filtered_items)
    items = filtered_items[skip:skip + limit]
    
    return {
        "items": items,
        "total": total
    }

@app.get("/backend/api/alerts/status/{status}")
@app.get("/api/alerts/status/{status}")
async def get_alerts_by_status(status: str, limit: int = 20, offset: int = 0):
    """Get alerts by status."""
    risk_levels = ["low", "medium", "high"]
    severities = ["low", "medium", "high", "critical"]
    
    total = 150
    alerts = [
        {
            "alert_id": offset + i + 1,
            "transaction_id": 1000 + offset + i,
            "risk_score": 50 + ((offset + i) % 50),
            "risk_level": risk_levels[(offset + i) % 3],
            "alert_severity": severities[(offset + i) % 4],
            "alert_status": status,
            "created_at": (datetime.utcnow() - timedelta(hours=(offset + i))).isoformat(),
        }
        for i in range(min(limit, total - offset))
    ]
    
    return {
        "alerts": alerts,
        "total": total
    }

@app.get("/backend/api/alerts/{alert_id}")
@app.get("/api/alerts/{alert_id}")
async def get_alert_detail(alert_id: int):
    """Get alert details."""
    return {
        "alert_id": alert_id,
        "transaction_id": 1000 + alert_id,
        "customer_id": 100000 + alert_id,
        "risk_score": 75,
        "risk_level": "high",
        "alert_status": "PENDING",
        "alert_severity": "high",
        "created_at": datetime.utcnow().isoformat(),
        "triggered_rules": ["rule_001", "rule_005", "rule_012"],
        "analyst_notes": None
    }

@app.put("/backend/api/alerts/{alert_id}/decide")
@app.put("/api/alerts/{alert_id}/decide")
async def decide_alert(alert_id: int, decision: str = "REJECTED", justification: str = ""):
    """Record an alert decision."""
    return {
        "alert_id": alert_id,
        "decision": decision,
        "decided_at": datetime.utcnow().isoformat(),
        "message": f"Alert {alert_id} decision recorded as {decision}"
    }

@app.get("/backend/api/analytics/customers")
@app.get("/api/analytics/customers")
async def get_customer_risks(limit: int = 20):
    """Get high-risk customer profiles."""
    customers = [
        {
            "customer_id": f"CUST-{100000 + i}",
            "total_transactions": 50 + (i * 5),
            "high_risk_count": 5 + (i % 10),
            "fraud_rate": round((i % 30) / 100, 2),
            "average_transaction_amount": 500 + (i * 50),
            "risk_profile": ["low", "medium", "high"][(i + 1) % 3],
            "suspicious_patterns": ["velocity_spike", "unusual_location", "midnight_transaction"][:((i % 3) + 1)]
        }
        for i in range(limit)
    ]
    
    return {
        "high_risk_customers": customers
    }

@app.get("/backend/api/analytics/anomalies")
@app.get("/api/analytics/anomalies")
async def get_anomalies():
    """Get recent anomaly signals."""
    anomalies = [
        {
            "type": "velocity_spike",
            "severity": "high",
            "description": "Customer CUST-100045 made 12 transactions in 30 minutes"
        },
        {
            "type": "geographic_anomaly",
            "severity": "medium",
            "description": "Transaction from Singapore 2 hours after transaction from NY"
        },
        {
            "type": "merchant_pattern",
            "severity": "low",
            "description": "First transaction with high-risk merchant category"
        },
        {
            "type": "amount_spike",
            "severity": "high",
            "description": "Transaction amount 5x higher than customer average"
        },
        {
            "type": "network_anomaly",
            "severity": "medium",
            "description": "VPN/proxy detected in transaction metadata"
        }
    ]
    
    return anomalies

@app.get("/backend/api/models")
@app.get("/api/models")
async def get_models():
    """Get trained models including persistent ones."""
    # Default models
    default_models = [
        {
            "id": "rf_v1_2024",
            "name": "random_forest",
            "version": "1.0",
            "training_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "dataset_size": 50000,
            "total_samples": 100000,
            "data_source": "database",
            "evaluation_only": False,
            "metrics": {
                "accuracy": 0.89,
                "precision": 0.87,
                "recall": 0.85,
                "f1_score": 0.86,
                "roc_auc": 0.92,
                "confusion_matrix": {"true_positive": 8500, "true_negative": 40500, "false_positive": 1500, "false_negative": 49500}
            },
            "cv_mean": 0.84,
            "feature_importance": [0.25, 0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.03, 0.02],
            "feature_names": ["transaction_amount", "customer_velocity", "merchant_risk_score", "geographic_distance", "time_of_day", "device_fingerprint", "ip_reputation", "account_age", "fraud_history"]
        }
    ]
    
    # Combine with trained models
    all_models = default_models + list(TRAINED_MODELS.values())
    
    return {
        "items": all_models
    }

# Global store for trained models
TRAINED_MODELS = {}

# Global store for detection rules - persistent across requests
DETECTION_RULES = {}

# Global store for team members - persistent across requests
TEAM_MEMBERS = {}

# Initialize global rules and team members on startup
def _initialize_data():
    """Initialize default rules and team members."""
    global DETECTION_RULES, TEAM_MEMBERS
    
    if not DETECTION_RULES:
        DETECTION_RULES = {
            f"rule_{i+1}": {
                "id": f"rule_{i+1}",
                "rule_id": f"RULE_VEL_{1000 + i}",
                "name": [
                    "High Velocity Transactions",
                    "Geographic Anomaly",
                    "Unusual Amount Pattern",
                    "Device Fingerprint Mismatch",
                    "Account Age Risk",
                    "IP Reputation Check",
                    "Time Zone Deviation",
                    "Multiple Failed Attempts",
                    "Merchant Category Mismatch",
                    "Customer Behavior Deviation"
                ][i % 10],
                "rule_type": [
                    "velocity_check",
                    "geographic_anomaly",
                    "amount_pattern",
                    "device_mismatch",
                    "account_age_risk",
                    "ip_reputation",
                    "timezone_deviation",
                    "auth_failure",
                    "merchant_category",
                    "behavior_deviation"
                ][i % 10],
                "description": [
                    "Detects unusually high transaction velocity",
                    "Flags transactions from unexpected locations",
                    "Identifies amounts outside normal range",
                    "Alerts on device changes",
                    "New accounts pose higher risk",
                    "Checks IP reputation scores",
                    "Monitors cross-timezone transactions",
                    "Tracks authentication failures",
                    "Monitors merchant category changes",
                    "Detects deviations from baseline behavior"
                ][i % 10],
                "severity": ["low", "medium", "high"][i % 3],
                "risk_weight": 80 - (i % 30),
                "threshold_value": 1000 + (i * 100) if i % 2 == 0 else None,
                "is_enabled": i % 2 == 0,
                "last_triggered": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "alert_count": 90 - (i % 100),
                "created_by": ["Admin User", "Analyst One"][i % 2],
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(days=i//2)).isoformat()
            }
            for i in range(20)
        }
    
    if not TEAM_MEMBERS:
        TEAM_MEMBERS = {
            f"user_{i+1}": {
                "id": i + 1,
                "full_name": ["Admin User", "Analyst One", "Viewer User", "John Analyst", "Sarah Admin"][i % 5],
                "email": ["admin@fraud-detection.local", "analyst@fraud-detection.local", "viewer@fraud-detection.local", "john@fraud-detection.local", "sarah@fraud-detection.local"][i % 5],
                "role": ["viewer", "analyst", "admin"][i % 3],
                "is_active": True
            }
            for i in range(20)
        }

_initialize_data()

@app.post("/backend/api/models/train")
@app.post("/api/models/train")
async def train_model(algorithms: list = None, source: str = "database", sample_limit: int = 1000):
    """Train a new model and persist it."""
    if algorithms is None:
        algorithms = ["random_forest"]
    
    models = []
    for algo in algorithms:
        model_id = f"model_{algo}_{int(datetime.utcnow().timestamp())}"
        model = {
            "id": model_id,
            "name": algo,
            "version": "1.0",
            "training_date": datetime.utcnow().isoformat(),
            "dataset_size": sample_limit,
            "total_samples": sample_limit * 2,
            "data_source": source,
            "evaluation_only": True,
            "feature_names": ["velocity_score", "amount_zscore", "device_entropy", "ip_reputation", "account_age_days", "auth_fail_count", "timezone_delta", "merchant_category_shift"],
            "feature_importance": [0.24, 0.17, 0.15, 0.13, 0.11, 0.09, 0.06, 0.04, 0.01],
            "metrics": {
                "accuracy": 0.88,
                "precision": 0.86,
                "recall": 0.84,
                "f1_score": 0.85,
                "roc_auc": 0.91,
                "confusion_matrix": {"true_positive": 8400, "true_negative": 40600, "false_positive": 1400, "false_negative": 49600}
            },
            "cv_mean": 0.83,
        }
        TRAINED_MODELS[model_id] = model
        models.append(model)
    
    return {
        "items": models,
        "total_samples": sample_limit * 2
    }

@app.get("/backend/api/users")
@app.get("/api/users")
async def get_users(skip: int = 0, limit: int = 20):
    """Get team members."""
    users = list(TEAM_MEMBERS.values())
    return users[skip:skip + limit]

@app.post("/backend/api/users")
@app.post("/api/users")
async def create_user(request: CreateTeamMemberRequest):
    """Create a new team member."""
    email_lower = request.email.lower()
    
    # Check if email already exists in TEAM_MEMBERS
    for user in TEAM_MEMBERS.values():
        if user["email"].lower() == email_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Also add to MOCK_USERS for login purposes
    if email_lower not in MOCK_USERS:
        new_id = max(u["id"] for u in MOCK_USERS.values()) + 1 if MOCK_USERS else 3
        MOCK_USERS[email_lower] = {
            "id": new_id,
            "email": email_lower,
            "password": request.password,
            "full_name": request.full_name,
            "role": request.role,
            "is_active": True
        }
    
    # Add to TEAM_MEMBERS
    team_id = max((u.get("id", 0) for u in TEAM_MEMBERS.values()), default=0) + 1
    new_user = {
        "id": team_id,
        "full_name": request.full_name,
        "email": email_lower,
        "role": request.role,
        "is_active": True
    }
    TEAM_MEMBERS[f"user_{team_id}"] = new_user
    logger.info(f"Created team member: {request.full_name} ({email_lower})")
    
    return {
        **new_user,
        "message": f"Team member {request.full_name} created successfully"
    }

@app.patch("/fraud/rules/{rule_id}")
@app.patch("/backend/fraud/rules/{rule_id}")
@app.patch("/api/rules/{rule_id}")
@app.patch("/backend/api/rules/{rule_id}")
async def update_rule(rule_id: str, request: UpdateRuleRequest = None):
    """Update a detection rule."""
    # If no request body is provided, try query parameters (for backwards compatibility)
    if request is None:
        request = UpdateRuleRequest()
    
    # Ensure we have rule_id with 'rule_' prefix if needed
    key = rule_id if rule_id.startswith('rule_') else f"rule_{rule_id}"
    
    if key not in DETECTION_RULES:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    rule = DETECTION_RULES[key]
    
    # Update only provided fields
    if request.is_enabled is not None:
        rule['is_enabled'] = request.is_enabled
    if request.name is not None:
        rule['name'] = request.name
    if request.description is not None:
        rule['description'] = request.description
    if request.threshold_value is not None:
        rule['threshold_value'] = request.threshold_value
    if request.risk_weight is not None:
        rule['risk_weight'] = request.risk_weight
    if request.severity is not None:
        rule['severity'] = request.severity
    
    rule['updated_at'] = datetime.utcnow().isoformat()
    
    return {
        **rule,
        "message": f"Rule {rule_id} updated successfully"
    }

@app.put("/fraud/rules/{rule_id}")
@app.put("/backend/fraud/rules/{rule_id}")
@app.put("/api/rules/{rule_id}")
@app.put("/backend/api/rules/{rule_id}")
async def update_rule_put(rule_id: str, request: UpdateRuleRequest = None):
    """Update a detection rule (PUT)."""
    # If no request body is provided, try query parameters (for backwards compatibility)
    if request is None:
        request = UpdateRuleRequest()
    
    # Ensure we have rule_id with 'rule_' prefix if needed
    key = rule_id if rule_id.startswith('rule_') else f"rule_{rule_id}"
    
    if key not in DETECTION_RULES:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    rule = DETECTION_RULES[key]
    
    # Update only provided fields
    if request.is_enabled is not None:
        rule['is_enabled'] = request.is_enabled
    if request.name is not None:
        rule['name'] = request.name
    if request.description is not None:
        rule['description'] = request.description
    if request.threshold_value is not None:
        rule['threshold_value'] = request.threshold_value
    if request.risk_weight is not None:
        rule['risk_weight'] = request.risk_weight
    if request.severity is not None:
        rule['severity'] = request.severity
    
    rule['updated_at'] = datetime.utcnow().isoformat()
    
    return {
        **rule,
        "message": f"Rule {rule_id} updated successfully"
    }

@app.patch("/backend/api/users/{user_id}")
@app.patch("/api/users/{user_id}")
@app.put("/backend/api/users/{user_id}")
@app.put("/api/users/{user_id}")
async def update_user(user_id: int, request: UpdateUserRequest = None):
    """Update a team member (deactivate, change role, etc.)."""
    if request is None:
        request = UpdateUserRequest()
    
    # Find user by ID
    user = None
    user_key = None
    for key, u in TEAM_MEMBERS.items():
        if u["id"] == user_id:
            user = u
            user_key = key
            break
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Update only provided fields
    if request.is_active is not None:
        user['is_active'] = request.is_active
    if request.role is not None:
        user['role'] = request.role
    
    return {
        **user,
        "message": f"User {user_id} {'deactivated' if request.is_active is False else 'updated'} successfully"
    }

@app.delete("/backend/api/users/{user_id}/deactivate")
@app.delete("/api/users/{user_id}/deactivate")
@app.post("/backend/api/users/{user_id}/deactivate")
@app.post("/api/users/{user_id}/deactivate")
async def deactivate_user(user_id: int):
    """Deactivate a team member."""
    # Find user by ID
    user = None
    for key, u in TEAM_MEMBERS.items():
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Deactivate user
    user['is_active'] = False
    
    return {
        **user,
        "message": f"User {user_id} deactivated successfully"
    }


@app.get("/fraud/rules")
@app.get("/backend/fraud/rules")
@app.get("/api/rules")
@app.get("/backend/api/rules")
async def get_rules(page: int = 1, limit: int = 20):
    """Get detection rules with pagination."""
    # Use global DETECTION_RULES storage
    all_rules = list(DETECTION_RULES.values())
    total = len(all_rules)
    offset = (page - 1) * limit
    rules = all_rules[offset:offset + limit]
    
    return {
        "data": rules,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@app.get("/backend/api/fraud-review")
@app.get("/api/fraud-review")
async def get_fraud_review(limit: int = 20, offset: int = 0):
    """Get fraud review queue data - alias for alerts/status."""
    status = "PENDING"
    risk_levels = ["low", "medium", "high"]
    severities = ["low", "medium", "high", "critical"]
    
    total = 150
    alerts = [
        {
            "alert_id": offset + i + 1,
            "transaction_id": 1000 + offset + i,
            "risk_score": 50 + ((offset + i) % 50),
            "risk_level": risk_levels[(offset + i) % 3],
            "alert_severity": severities[(offset + i) % 4],
            "alert_status": status,
            "created_at": (datetime.utcnow() - timedelta(hours=(offset + i))).isoformat(),
        }
        for i in range(min(limit, total - offset))
    ]
    
    return {
        "alerts": alerts,
        "total": total
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Mock Backend Server")
    logger.info("Test Credentials:")
    logger.info("  Email: admin@fraud-detection.local")
    logger.info("  Password: password")
    logger.info("")
    logger.info("  Email: analyst@fraud-detection.local")
    logger.info("  Password: password")
    logger.info("")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="info"
    )
