# Financial Risk Analysis and Hybrid Fraud Detection System

A production-grade Python application for detecting financial fraud using a combination of rule-based detection and machine learning, with comprehensive risk scoring and analyst review workflows.

## Features

### Core Capabilities
- **Rule-Based Fraud Detection**: Configurable rules stored in database (high-value transactions, velocity checks, geographic anomalies, duplicates, etc.)
- **Machine Learning Detection**: Logistic Regression, Random Forest, and Isolation Forest models with proper evaluation metrics
- **Financial Risk Scoring**: Explainable 0-100 risk scores combining multiple signals
- **Real-Time Fraud Assessment**: Hybrid pipeline for immediate detection on transaction creation
- **Comprehensive Audit Logging**: Complete forensic trail of all system actions
- **Role-Based Access Control**: Admin and analyst roles with granular permissions

### User Interface
- **FastAPI Backend**: RESTful API with JWT authentication and OpenAPI documentation
- **Modern React Console**: Responsive risk operations workspace at http://localhost:3000; see [frontend setup and training](frontend/README.md)
- **Streamlit Dashboard**: Interactive web interface for analysts and administrators
- **Responsive Design**: Professional analytics theme with real-time dashboards
- **Transaction Explorer**: Search, filter, and export transaction data
- **Fraud Alerts**: Analyst review queue with decision tracking

### Data Support
- **Public Dataset**: Credit Card Fraud Detection from Kaggle (requires manual download)
- **Synthetic Data Generation**: Realistic transaction generation with controlled fraud scenarios
- **Batch Import**: CSV import with validation and deduplication
- **Multiple Payment Methods**: Cards, bank transfers, wallets, and more

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.12+ |
| **Backend Framework** | FastAPI | 0.104+ |
| **Frontend** | Streamlit | 1.29+ |
| **Database** | MySQL | 8.0+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Authentication** | JWT + Argon2 | PyJWT 2.15+, Argon2 25.1+ |
| **Data Processing** | Pandas, NumPy | 2.1+, 1.26+ |
| **Machine Learning** | Scikit-learn, Imbalanced-learn | 1.3+, 0.11+ |
| **Visualization** | Plotly | 5.18+ |

## Project Structure

```
financial-risk-fraud-detection/
├── app/                          # Main application package
│   ├── main.py                   # FastAPI entry point
│   ├── core/                     # Core configuration and security
│   │   ├── config.py             # Settings management
│   │   ├── security.py           # JWT and password utilities
│   │   └── permissions.py        # Role-based access control
│   ├── db/                       # Database layer
│   │   ├── database.py           # SQLAlchemy engine and sessions
│   │   └── base.py               # Base model class
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py               # User and authentication
│   │   ├── customer.py           # Customer information
│   │   ├── transaction.py        # Financial transactions
│   │   ├── fraud_rule.py         # Configurable fraud rules
│   │   ├── fraud_alert.py        # Alerts and assessments
│   │   └── audit_log.py          # Audit trail
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── api/                      # API route handlers
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── transactions.py       # Transaction management
│   │   ├── fraud.py              # Fraud detection and alerts
│   │   ├── analytics.py          # Analytics and reporting
│   │   ├── users.py              # User management
│   │   └── audit.py              # Audit log endpoints
│   ├── services/                 # Business logic services
│   │   ├── audit_service.py      # Audit logging
│   │   ├── transaction_service.py # Transaction processing
│   │   ├── fraud_engine.py       # Rule-based detection
│   │   ├── risk_engine.py        # Risk scoring
│   │   └── ml_service.py         # ML model management
│   └── ml/                       # Machine learning pipeline
│       ├── preprocessing.py      # Feature engineering
│       ├── train.py              # Model training
│       ├── predict.py            # Predictions
│       └── evaluate.py           # Model evaluation
├── dashboard/                    # Streamlit frontend
│   ├── app.py                    # Dashboard entry point
│   ├── pages/                    # Dashboard pages
│   │   ├── 01_Login.py           # Authentication
│   │   ├── 02_Executive_Overview.py
│   │   ├── 03_Transaction_Explorer.py
│   │   ├── 04_Fraud_Alerts.py
│   │   ├── 05_Financial_Risk_Analytics.py
│   │   ├── 06_Rule_Management.py (admin only)
│   │   ├── 07_Model_Performance.py
│   │   ├── 08_User_Management.py  (admin only)
│   │   └── 09_Audit_Logs.py
│   └── components/               # Reusable components
│       ├── charts.py
│       ├── filters.py
│       └── auth_handler.py
├── scripts/                      # Utility scripts
│   ├── init_db.py                # Database initialization
│   ├── create_admin.py           # Create admin user
│   ├── generate_synthetic_data.py # Synthetic transaction generation
│   ├── import_public_dataset.py  # Kaggle dataset import
│   ├── seed_rules.py             # Default rule creation
│   └── train_model.py            # ML model training
├── tests/                        # Test suite
│   ├── test_auth.py              # Authentication tests
│   ├── test_transactions.py      # Transaction API tests
│   ├── test_fraud_rules.py       # Rule engine tests
│   ├── test_risk_scoring.py      # Risk scoring tests
│   ├── test_ml.py                # ML pipeline tests
│   └── test_audit.py             # Audit logging tests
├── data/                         # Data files
│   ├── raw/                      # Raw data (CSVs, datasets)
│   └── processed/                # Processed data
├── models/                       # Trained ML models
├── reports/                      # Analysis reports
├── migrations/                   # Alembic database migrations
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── run.py                        # Application launcher
├── README.md                     # This file
└── ARCHITECTURE.md               # Architecture documentation

```

## Quick Start

### Prerequisites
- Python 3.12 or later
- MySQL 8.0 or later
- pip (Python package manager)

### Installation

1. **Clone or download the project**
```bash
cd Financial\ Risk\ Analysis\ and\ Hybrid\ Fraud\ Detection\ System
```

2. **Create a virtual environment (optional but recommended)**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize the database**
```bash
python scripts/init_db.py
# Follow prompts to create database and user
```

6. **Create admin user**
```bash
python scripts/create_admin.py
```

7. **Seed default fraud rules**
```bash
python scripts/seed_rules.py
```

### Running the Application

**Terminal 1: Start FastAPI backend**
```bash
python run.py
# Or: uvicorn app.main:app --reload
```
Backend will be available at: `http://127.0.0.1:8000`

**Terminal 2: Start Streamlit dashboard**
```bash
streamlit run dashboard/app.py
```
Dashboard will be available at: `http://localhost:8501`

### API Documentation

Once the backend is running, visit:
- **OpenAPI (Swagger)**: `http://127.0.0.1:8000/api/docs`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc`

## Key Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### Transactions
- `GET /transactions` - List transactions with filtering
- `POST /transactions` - Create transaction
- `POST /transactions/import` - Batch CSV import
- `GET /transactions/{transaction_id}` - Get transaction details
- `POST /transactions/{transaction_id}/assess` - Trigger fraud assessment

### Fraud Detection
- `GET /fraud/alerts` - List fraud alerts
- `GET /fraud/alerts/{alert_id}` - Alert details
- `POST /fraud/alerts/{alert_id}/review` - Analyst review

### Rules
- `GET /rules` - List fraud rules
- `POST /rules` - Create rule (admin)
- `PATCH /rules/{rule_id}` - Update rule (admin)

### Analytics
- `GET /analytics/overview` - Overview dashboard metrics
- `GET /analytics/risk-trends` - Risk trends over time
- `GET /analytics/model-performance` - ML model metrics

### Audit
- `GET /audit-logs` - Audit trail

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Database
DATABASE_URL=mysql+pymysql://fraud_user:password@localhost:3306/fraud_detection_db
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fraud_detection_db
DB_USER=fraud_user
DB_PASSWORD=your_secure_password

# JWT
SECRET_KEY=your_super_secret_key_minimum_32_characters
JWT_EXPIRATION_HOURS=24

# FastAPI
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
DEBUG=True
ENVIRONMENT=development

# Streamlit
STREAMLIT_SERVER_PORT=8501
API_BASE_URL=http://127.0.0.1:8000

# ML
ENABLE_ML_DETECTION=True
ML_MODEL_THRESHOLD=0.5
```

## Database Schema

### Core Tables

- **users**: User accounts with roles and authentication
- **customers**: Customer/account holder information
- **transactions**: Financial transactions with status and metadata
- **fraud_rules**: Configurable detection rules
- **fraud_assessments**: Risk scores and detection results
- **triggered_rules**: Rules triggered per transaction
- **fraud_alerts**: High-risk alerts for analyst review
- **audit_logs**: Complete action audit trail

### Relationships
```
User → AuditLog (actor)
Customer → Transaction
Customer → FraudAlert
Transaction → FraudAssessment
Transaction → TriggeredRule
Transaction → FraudAlert
FraudRule → TriggeredRule
FraudAssessment → TriggeredRule
FraudAssessment → FraudAlert
```

## Fraud Detection Rules

### Implemented Rules

| ID | Name | Description | Severity |
|----|----|---|----------|
| R01 | High-Value Transaction | Amount exceeds configurable threshold | High |
| R02 | Transaction Velocity | Multiple transactions in time window | Medium |
| R03 | Unusual Amount | Deviation from customer baseline | High |
| R04 | Repeated Failures | Failed transactions pattern | Medium |
| R05 | Geographic Anomaly | Impossible travel scenarios | Critical |
| R06 | Duplicate Transaction | Potential duplicate based on amount/merchant/time | High |
| R07 | High Velocity | Many transactions in short interval | High |
| R08 | Unusual Hours | Transaction at abnormal time | Low |
| R09 | New Device/Merchant | First interaction with device or merchant | Medium |
| R10 | Distribution Deviation | Unusual pattern in customer data | Medium |

### Rule Engine Features
- Database-driven configuration (no code changes needed)
- Threshold customization per rule
- Enable/disable controls
- Severity levels and risk weights
- Detailed trigger explanations
- Graceful handling of missing fields

## Machine Learning Pipeline

### Supported Models
1. **Logistic Regression** - Baseline linear model
2. **Random Forest** - Nonlinear ensemble model
3. **Isolation Forest** - Unsupervised anomaly detection (optional)

### Evaluation Metrics
- Precision, Recall, F1-Score
- ROC-AUC, PR-AUC
- Confusion Matrix
- False Positive Rate

### Data Handling
- Chronological train/test split
- Class weight balancing
- Feature normalization
- Prevention of data leakage

### Model Evaluation
```bash
python scripts/train_model.py
```

## Security Features

### Authentication & Authorization
- JWT-based token authentication with expiration
- Argon2 password hashing (memory-hard, GPU-resistant)
- Role-based access control (Admin, Analyst, Viewer)
- Granular permission checks

### Data Protection
- SQL injection protection via SQLAlchemy
- Request validation with Pydantic
- File upload size limits
- Safe CSV export against formula injection
- No logging of sensitive data (passwords, tokens, PII)

### Audit Trail
- Comprehensive logging of all actions
- Actor identification and request context
- Immutable audit log (append-only)
- Chained event tracking via request IDs

### Best Practices
- Environment-based secrets (never hardcoded)
- HTTPS enforcement in production
- CORS configuration
- Rate limiting ready (deploy-level)
- Secure password reset workflow (implement per deployment)

## Testing

### Run Tests
```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html  # With coverage
```

### Test Coverage
- Authentication and token validation
- Password verification
- Transaction creation and import
- Fraud rule evaluation
- Risk scoring logic
- ML model training and prediction
- Alert generation
- Audit logging
- Database constraints

## Data Import

### Synthetic Data Generation
```bash
python scripts/generate_synthetic_data.py --count 50000
```

### Public Dataset Import
1. Download from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
2. Place `creditcard.csv` in `data/raw/`
3. Run:
```bash
python scripts/import_public_dataset.py
```

## Logging

Logs are written to:
- Console (development)
- `logs/app.log` (configured in settings)

Log levels: DEBUG, INFO, WARNING, ERROR

## Production Deployment

### Critical Changes Required
1. **Set DEBUG=False** in environment
2. **Use strong SECRET_KEY** (minimum 32 characters, cryptographically random)
3. **Use HTTPS** with valid SSL certificates
4. **Database User**: Ensure minimal permissions (SELECT/INSERT/UPDATE only)
5. **Secrets Management**: Use AWS Secrets Manager, Azure KeyVault, or HashiCorp Vault
6. **Rate Limiting**: Deploy behind reverse proxy with rate limiting
7. **Monitoring**: Implement application monitoring (APM)
8. **Backups**: Regular encrypted database backups
9. **Audit**: External audit log archive
10. **API Gateway**: Consider API gateway for rate limiting and DDoS protection

### Deployment Options
- **Docker**: Container-based deployment
- **AWS**: ECS, RDS for MySQL, CloudFront for CDN
- **Azure**: App Service, Azure Database for MySQL, Azure Front Door
- **On-Premises**: K8s cluster with external MySQL database

## Limitations & Future Improvements

### Known Limitations
- Single-model inference (ensemble predictions as future work)
- In-memory model storage (migrate to shared storage for scaling)
- Basic rate limiting (implement Redis-based throttling)
- No multi-tenancy support
- Transaction immutability relies on database (consider blockchain for critical audits)
- ML models trained on historical data only (no online learning)

### Future Enhancements
1. Real-time model retraining pipeline
2. Multi-model ensemble predictions
3. Feature store integration
4. Distributed fraud detection (Kafka streaming)
5. Advanced explainability (SHAP, LIME)
6. Behavioral biometrics
7. Network analysis for fraud rings
8. Mobile app for on-the-go analyst reviews
9. Integration with external risk services
10. Automated fraud recovery workflows

## Troubleshooting

### Database Connection Issues
```bash
# Test MySQL connectivity
mysql -h localhost -u fraud_user -p fraud_detection_db -e "SELECT 1;"

# Check connection string in .env
# Ensure MySQL service is running
# Verify firewall rules
```

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Check Python path
echo $PYTHONPATH
# Add project root if needed: set PYTHONPATH=%cd%
```

### Dashboard Connection Issues
```bash
# Verify FastAPI is running on configured port
# Check CORS settings in .env
# Clear browser cache
# Test API directly: curl http://127.0.0.1:8000/health
```

### Model Training Failures
```bash
# Check data/raw/creditcard.csv exists
# Verify data format matches Kaggle dataset
# Check scikit-learn version compatibility
```

## Contributing

Contributions welcome! Areas for contribution:
- Additional fraud rules
- UI/UX improvements
- Performance optimization
- Additional test coverage
- Documentation improvements
- Integration examples

## License

This project is provided as-is for educational and portfolio purposes.

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Review the API documentation at `/api/docs`
3. Check audit logs for debugging
4. Consult the architecture document

## Acknowledgments

- Credit Card Fraud Detection dataset from Kaggle (MLG-ULB)
- FastAPI framework and documentation
- Streamlit for rapid dashboard development
- SQLAlchemy for ORM excellence

---

**Version**: 1.0.0  
**Last Updated**: October 2026  
**Status**: Phase 1-3 Completed, Phases 4-10 Pending
