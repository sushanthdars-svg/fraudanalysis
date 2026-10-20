# API Reference

## Financial Risk Analysis & Hybrid Fraud Detection System

Complete API documentation for all endpoints.

## Base URL

```
http://localhost:8000
Production: https://api.yourdomain.com
```

## Authentication

All endpoints (except `/health` and `/login`) require JWT authentication.

### Login Endpoint

**POST** `/api/v1/auth/login`

Request:
```json
{
  "username": "admin@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

Use token in Authorization header:
```
Authorization: Bearer <token>
```

## Health Endpoints

### Health Check

**GET** `/health`

Returns basic health status.

Response: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Readiness Check

**GET** `/health/ready`

Checks all dependencies (database, cache, etc.).

Response: `200 OK` if ready, `503 Service Unavailable` if not.

```json
{
  "status": "ready",
  "database": "connected",
  "cache": "connected"
}
```

### Liveness Check

**GET** `/health/live`

Basic liveness probe for Kubernetes.

Response: `200 OK` if alive.

## Transaction Endpoints

### Upload Transactions

**POST** `/api/v1/transactions/upload`

Upload bulk transactions for fraud detection.

Request:
```json
{
  "transactions": [
    {
      "transaction_id": "TXN001",
      "customer_id": "CUST001",
      "merchant_id": "MERCH001",
      "amount": 150.00,
      "currency": "USD",
      "transaction_type": "purchase",
      "timestamp": "2024-01-01T10:00:00Z",
      "location": "US",
      "ip_address": "192.168.1.1",
      "device_id": "DEVICE001"
    }
  ]
}
```

Response: `200 OK`
```json
{
  "processed": 1,
  "failed": 0,
  "alerts_generated": 0
}
```

### Get Transactions

**GET** `/api/v1/transactions`

Query transactions with filtering and pagination.

Parameters:
- `page`: Page number (default: 1)
- `limit`: Records per page (default: 50, max: 1000)
- `status`: Filter by status (completed, pending, failed)
- `start_date`: ISO date filter
- `end_date`: ISO date filter

Response: `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "transaction_id": "TXN001",
      "customer_id": "CUST001",
      "amount": 150.00,
      "status": "completed",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 50
}
```

### Get Transaction Details

**GET** `/api/v1/transactions/{transaction_id}`

Response: `200 OK`
```json
{
  "id": 1,
  "transaction_id": "TXN001",
  "customer_id": "CUST001",
  "merchant_id": "MERCH001",
  "amount": 150.00,
  "currency": "USD",
  "transaction_type": "purchase",
  "status": "completed",
  "location": "US",
  "ip_address": "192.168.1.1",
  "device_id": "DEVICE001",
  "timestamp": "2024-01-01T10:00:00Z",
  "risk_score": 25.5
}
```

## Alert Endpoints

### Get Alerts

**GET** `/api/v1/alerts`

Query fraud alerts.

Parameters:
- `page`: Page number (default: 1)
- `limit`: Records per page (default: 50, max: 1000)
- `status`: open, investigating, closed
- `severity`: low, medium, high, critical
- `start_date`: ISO date filter

Response: `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "alert_id": "ALERT001",
      "transaction_id": "TXN001",
      "customer_id": "CUST001",
      "severity": "high",
      "risk_score": 85.5,
      "status": "open",
      "created_at": "2024-01-01T10:05:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50
}
```

### Update Alert Status

**PATCH** `/api/v1/alerts/{alert_id}`

Request:
```json
{
  "status": "investigating",
  "assigned_to": "investigator@example.com"
}
```

Response: `200 OK`
```json
{
  "id": 1,
  "alert_id": "ALERT001",
  "status": "investigating",
  "updated_at": "2024-01-01T10:10:00Z"
}
```

## Investigation Case Endpoints

### Create Investigation Case

**POST** `/api/v1/cases`

Request:
```json
{
  "alert_id": 1,
  "case_type": "fraud",
  "priority": "high",
  "assigned_to": "investigator@example.com",
  "notes": "Suspicious transaction pattern detected"
}
```

Response: `201 Created`
```json
{
  "id": 1,
  "case_id": "CASE001",
  "alert_id": 1,
  "status": "open",
  "created_at": "2024-01-01T10:15:00Z"
}
```

### Get Investigation Cases

**GET** `/api/v1/cases`

Parameters:
- `page`: Page number
- `status`: open, investigating, closed, escalated
- `priority`: low, medium, high
- `assigned_to`: Assignee filter

Response: `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE001",
      "status": "investigating",
      "priority": "high",
      "created_at": "2024-01-01T10:15:00Z"
    }
  ],
  "total": 10,
  "page": 1
}
```

### Update Case Status

**PATCH** `/api/v1/cases/{case_id}`

Request:
```json
{
  "status": "closed",
  "resolution": "Legitimate transaction after customer verification",
  "resolution_type": "false_positive"
}
```

Response: `200 OK`

## Risk Assessment Endpoints

### Get Risk Score

**POST** `/api/v1/risk/score`

Request:
```json
{
  "customer_id": "CUST001",
  "transaction_data": {
    "amount": 5000,
    "location": "CN",
    "transaction_type": "wire_transfer"
  }
}
```

Response: `200 OK`
```json
{
  "customer_id": "CUST001",
  "risk_score": 75.5,
  "risk_level": "high",
  "factors": [
    {
      "name": "Unusual location",
      "weight": 0.4,
      "score": 85
    },
    {
      "name": "High amount",
      "weight": 0.3,
      "score": 70
    }
  ]
}
```

### Get Customer Risk Profile

**GET** `/api/v1/risk/customers/{customer_id}`

Response: `200 OK`
```json
{
  "customer_id": "CUST001",
  "overall_risk": "medium",
  "transaction_risk": 45.5,
  "behavioral_risk": 35.2,
  "last_assessment": "2024-01-01T11:00:00Z"
}
```

## Dashboard Endpoints

### Get Dashboard Summary

**GET** `/api/v1/dashboard/summary`

Response: `200 OK`
```json
{
  "total_transactions": 10000,
  "total_alerts": 150,
  "high_risk_customers": 25,
  "open_cases": 12,
  "avg_risk_score": 42.5,
  "fraud_rate": 1.5
}
```

### Get Recent Alerts

**GET** `/api/v1/dashboard/alerts/recent`

Response: `200 OK`
```json
{
  "alerts": [
    {
      "alert_id": "ALERT001",
      "severity": "critical",
      "timestamp": "2024-01-01T11:00:00Z"
    }
  ],
  "count": 5
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "bad_request",
  "message": "Invalid request parameters",
  "details": ["amount must be positive"]
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req-123456"
}
```

## Rate Limiting

- Standard endpoints: 100 requests per hour
- Bulk upload: 10 requests per hour
- Authentication: 5 failed attempts per 5 minutes

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641038400
```

## Code Examples

### Python

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
    "username": "admin@example.com",
    "password": "password"
})
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get alerts
response = requests.get(f"{BASE_URL}/api/v1/alerts", headers=headers)
alerts = response.json()

print(f"Found {len(alerts['data'])} alerts")
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get alerts
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN"
```

### JavaScript/Node.js

```javascript
const baseUrl = 'http://localhost:8000';

async function getAlerts() {
  // Login
  const loginRes = await fetch(`${baseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin@example.com',
      password: 'password'
    })
  });
  const { access_token } = await loginRes.json();

  // Get alerts
  const res = await fetch(`${baseUrl}/api/v1/alerts`, {
    headers: { 'Authorization': `Bearer ${access_token}` }
  });
  const data = await res.json();
  console.log(`Found ${data.data.length} alerts`);
}

getAlerts();
```

## Webhooks (Optional)

Subscribe to events via webhooks:

**POST** `/api/v1/webhooks`

Request:
```json
{
  "event": "alert.created",
  "url": "https://your-server.com/webhook",
  "active": true
}
```

Events:
- `alert.created`: New alert generated
- `alert.status_changed`: Alert status updated
- `case.created`: New investigation case
- `case.closed`: Investigation case closed

---

**Version**: 1.0.0
**Last Updated**: 2024-01-01
