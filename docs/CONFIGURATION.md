# Configuration Reference

## Financial Risk Analysis & Hybrid Fraud Detection System

Complete reference for all environment variables and configuration options.

## Table of Contents

1. [Required Variables](#required-variables)
2. [Database Configuration](#database-configuration)
3. [Security Configuration](#security-configuration)
4. [API Configuration](#api-configuration)
5. [Dashboard Configuration](#dashboard-configuration)
6. [Redis Configuration](#redis-configuration)
7. [Logging Configuration](#logging-configuration)
8. [ML Model Configuration](#ml-model-configuration)
9. [Production Recommendations](#production-recommendations)

## Required Variables

These variables must be set for the system to function:

### Core Settings

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `ENVIRONMENT` | string | Deployment environment | `production` \| `staging` \| `development` |
| `DEBUG` | bool | Enable debug mode (NEVER true in production) | `false` |
| `SECRET_KEY` | string | Application secret key (min 32 chars) | `your-secret-key-...` |
| `API_HOST` | string | API server listen address | `0.0.0.0` |
| `API_PORT` | int | API server port | `8000` |
| `API_BASE_URL` | string | Public API URL | `https://api.yourdomain.com` |

## Database Configuration

### MySQL Connection

```bash
# Connection string format
DATABASE_URL=mysql+pymysql://username:password@host:port/database

# Example
DATABASE_URL=mysql+pymysql://fraud_user:secure_password@mysql:3306/fraud_detection

# Windows with MySQL
DATABASE_URL=mysql+pymysql://fraud_user:secure_password@localhost:3306/fraud_detection
```

### Connection Pool Settings

| Variable | Default | Min | Max | Description |
|----------|---------|-----|-----|-------------|
| `DB_POOL_SIZE` | 10 | 5 | 50 | Maximum pool connections |
| `DB_POOL_MAX_OVERFLOW` | 10 | 0 | 100 | Overflow connections |
| `DB_POOL_TIMEOUT` | 30 | 5 | 120 | Connection timeout (seconds) |
| `DB_POOL_RECYCLE` | 3600 | 1800 | 7200 | Recycle connections (seconds) |
| `DB_POOL_PRE_PING` | true | - | - | Test connection before use |
| `DB_ECHO` | false | - | - | Log all SQL statements |

### Production Recommendations

```bash
# Production database settings
DATABASE_URL=mysql+pymysql://user:strong_password@db.example.com:3306/fraud_detection
DB_POOL_SIZE=20          # Handle concurrent requests
DB_POOL_RECYCLE=3600     # Recycle stale connections
DB_POOL_TIMEOUT=30       # Reasonable timeout
DB_POOL_PRE_PING=true    # Avoid dead connections
DB_ECHO=false            # No SQL logging
```

## Security Configuration

### JWT Authentication

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JWT_SECRET_KEY` | `SECRET_KEY` | JWT signing key | Same as `SECRET_KEY` |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm | `HS256` \| `RS256` |
| `JWT_EXPIRATION_HOURS` | 24 | Token expiration | 24 |
| `JWT_REFRESH_EXPIRATION_DAYS` | 7 | Refresh token expiration | 7 |

### CORS Settings

```bash
# Allowed origins (comma-separated)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# CORS settings
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization
CORS_MAX_AGE=3600
```

### HTTPS/TLS

```bash
# Enforce HTTPS
ENFORCE_HTTPS=true
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000

# SSL Certificate paths (if using custom certs)
SSL_CERT_FILE=/etc/ssl/certs/your-cert.crt
SSL_KEY_FILE=/etc/ssl/private/your-key.key
```

### Password Policy

```bash
# Password requirements
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true

# Session settings
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | true | Enable rate limiting |
| `RATE_LIMIT_REQUESTS` | 100 | Requests per period |
| `RATE_LIMIT_PERIOD_SECONDS` | 3600 | Rate limit period (1 hour) |
| `RATE_LIMIT_PER_IP` | true | Limit per IP or user |

### Production Security Template

```bash
# .env.production (NEVER commit!)
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
DEBUG=false
ENVIRONMENT=production
ENFORCE_HTTPS=true
ALLOWED_ORIGINS=https://yourdomain.com

# Strong password policy
PASSWORD_MIN_LENGTH=14
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=3600
```

## API Configuration

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_WORKERS` | 4 | Number of worker processes |
| `API_THREADS` | 1 | Threads per worker |
| `REQUEST_TIMEOUT` | 30 | Request timeout (seconds) |
| `MAX_REQUEST_SIZE` | 10 | Max request body size (MB) |
| `KEEP_ALIVE` | 5 | Keep-alive timeout (seconds) |

### Pagination

```bash
# Pagination defaults
PAGINATION_DEFAULT_LIMIT=50
PAGINATION_MAX_LIMIT=1000
PAGINATION_MIN_LIMIT=1
```

### Transaction Processing

```bash
# Bulk upload limits
BULK_UPLOAD_MAX_RECORDS=10000
BULK_UPLOAD_TIMEOUT_SECONDS=300
BULK_UPLOAD_BATCH_SIZE=1000

# Transaction limits
TRANSACTION_MIN_AMOUNT=0.01
TRANSACTION_MAX_AMOUNT=999999.99
```

## Dashboard Configuration

### Streamlit Settings

```bash
# Streamlit server configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
STREAMLIT_SERVER_ENABLE_CORS=false

# Dashboard UI settings
STREAMLIT_LOGGER_LEVEL=info
STREAMLIT_CLIENT_LOGGER_LEVEL=info
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
```

### Dashboard Features

```bash
# Feature toggles
ENABLE_TRANSACTION_UPLOAD=true
ENABLE_ALERTS_DASHBOARD=true
ENABLE_INVESTIGATION_CASES=true
ENABLE_RISK_ASSESSMENT=true
ENABLE_ML_MODELS=true
ENABLE_AUDIT_LOG_VIEWER=true

# Dashboard refresh intervals (seconds)
ALERTS_REFRESH_INTERVAL=60
CASES_REFRESH_INTERVAL=120
METRICS_REFRESH_INTERVAL=300
```

## Redis Configuration

### Connection Settings

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Or individual settings
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password

# Connection pool
REDIS_POOL_SIZE=10
REDIS_POOL_TIMEOUT=5
REDIS_CONNECTION_TIMEOUT=5
```

### Caching Strategy

```bash
# Cache TTLs (Time to Live in seconds)
CACHE_TTL_ALERTS=300        # 5 minutes
CACHE_TTL_RISK_SCORE=600    # 10 minutes
CACHE_TTL_CUSTOMER_PROFILE=1800  # 30 minutes
CACHE_TTL_FRAUD_RULES=3600  # 1 hour

# Cache prefixes
CACHE_KEY_PREFIX=fraud_detection:
```

## Logging Configuration

### Log Levels

```bash
# Application log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Component-specific levels
LOG_LEVEL_API=INFO
LOG_LEVEL_DATABASE=INFO
LOG_LEVEL_ML=DEBUG
LOG_LEVEL_FRAUD_DETECTION=INFO
```

### Log Output

```bash
# Log file configuration
LOG_FILE=/app/logs/app.log
LOG_FORMAT=json  # json or text
LOG_BACKUP_COUNT=7  # Keep 7 backup files
LOG_MAX_SIZE=104857600  # 100MB per file

# Console logging
LOG_CONSOLE_ENABLED=true
LOG_CONSOLE_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Structured Logging

```bash
# Include context in logs
LOG_INCLUDE_REQUEST_ID=true
LOG_INCLUDE_USER_ID=true
LOG_INCLUDE_PERFORMANCE_METRICS=true
LOG_INCLUDE_AUDIT_INFO=true
```

## ML Model Configuration

### Model Settings

```bash
# Model directories
ML_MODEL_DIR=/app/models
ML_FRAUD_MODEL=fraud_detection_model.pkl
ML_RISK_MODEL=risk_assessment_model.pkl

# Model versioning
ML_MODEL_VERSION=1.0.0
ML_MODEL_ENABLE_AUTO_UPDATE=false

# Prediction confidence
ML_MIN_CONFIDENCE_THRESHOLD=0.65
ML_HIGH_CONFIDENCE_THRESHOLD=0.85
```

### Feature Configuration

```bash
# Feature engineering
ML_ENABLE_FEATURE_SCALING=true
ML_FEATURE_SCALING_METHOD=StandardScaler

# Training data
ML_TRAINING_DATA_PATH=/app/data/training/
ML_HOLDOUT_PERCENTAGE=20
ML_RANDOM_STATE=42
```

## Production Recommendations

### Minimum Production .env

```bash
# ============================================
# PRODUCTION CONFIGURATION (.env.production)
# ============================================

# Core
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-strong-key>
API_BASE_URL=https://api.yourdomain.com

# Database (use managed service like RDS)
DATABASE_URL=mysql+pymysql://user:password@db.yourregion.rds.amazonaws.com:3306/fraud_detection
DB_POOL_SIZE=20
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Security
JWT_EXPIRATION_HOURS=24
ENFORCE_HTTPS=true
ALLOWED_ORIGINS=https://yourdomain.com
PASSWORD_MIN_LENGTH=12
RATE_LIMIT_ENABLED=true

# API
API_WORKERS=8
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/fraud-detection/app.log

# Redis (optional, for caching)
REDIS_URL=redis://redis.yourdomain.com:6379/0

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Environment Variables Checklist

**Before Production Deployment**:

- [ ] `ENVIRONMENT=production` (NOT staging/development)
- [ ] `DEBUG=false` (NEVER true in production)
- [ ] `SECRET_KEY` is strong (32+ random characters)
- [ ] `DATABASE_URL` points to production database
- [ ] `ALLOWED_ORIGINS` contains only production domains
- [ ] `ENFORCE_HTTPS=true`
- [ ] `LOG_LEVEL=WARNING` (not DEBUG)
- [ ] `API_WORKERS` >= 4 (depends on CPU cores)
- [ ] All sensitive keys are in `.env` (NOT in code)
- [ ] `.env` is in `.gitignore` (NOT committed)

### Configuration Validation

```bash
# Validate configuration before startup
python -c "from app.core.config import settings; print(settings)"

# Check specific settings
python -c "from app.core.config import settings; print(f'Debug: {settings.DEBUG}')"
```

---

**Version**: 1.0.0
**Last Updated**: 2024-01-01

## See Also

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [OPERATIONS.md](./OPERATIONS.md) - Operations guide
- [API_REFERENCE.md](./API_REFERENCE.md) - API documentation
