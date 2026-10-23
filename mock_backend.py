#!/usr/bin/env python
"""Mock backend API server to support frontend development.

This bypasses the SQLAlchemy DLL loading issue by providing
a minimal FastAPI server with mock authentication endpoints.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import json
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
    email: str
    password: str

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
async def login(request: LoginRequest) -> LoginResponse:
    """
    Login endpoint - mock version.
    
    Default test credentials:
    - Email: admin@fraud-detection.local
    - Password: password
    
    - Email: analyst@fraud-detection.local
    - Password: password
    """
    email = request.email.lower()
    
    # Find user
    user = MOCK_USERS.get(email)
    if not user or user["password"] != request.password:
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
async def register(request: LoginRequest):
    """Register endpoint - mock version."""
    email = request.email.lower()
    
    if email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user_id = max(u["id"] for u in MOCK_USERS.values()) + 1
    new_user = {
        "id": user_id,
        "email": email,
        "password": request.password,
        "full_name": "New User",
        "role": "analyst",
        "is_active": True
    }
    MOCK_USERS[email] = new_user
    
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
    """Get ML models list."""
    return {
        "models": [
            {
                "id": 1,
                "name": "Gradient Boosting Model",
                "type": "classification",
                "accuracy": 0.972,
                "precision": 0.95,
                "recall": 0.91,
                "f1_score": 0.93,
                "status": "active",
                "deployed_date": "2024-01-15",
                "version": "2.1.0"
            },
            {
                "id": 2,
                "name": "Random Forest Model",
                "type": "classification",
                "accuracy": 0.948,
                "precision": 0.92,
                "recall": 0.87,
                "f1_score": 0.89,
                "status": "active",
                "deployed_date": "2023-11-20",
                "version": "1.8.0"
            }
        ]
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
async def get_audit_logs(skip: int = 0, limit: int = 20):
    """Get audit logs."""
    actions = ["login", "alert_resolved", "model_updated", "config_changed"]
    logs = [
        {
            "id": i,
            "user_email": "admin@fraud-detection.local",
            "action": actions[i % len(actions)],
            "resource": f"Transaction {1000 + i}",
            "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
            "details": f"Action {i} performed successfully"
        }
        for i in range(1, limit + 1)
    ]
    return {
        "total": 5_000,
        "logs": logs,
        "skip": skip,
        "limit": limit
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
