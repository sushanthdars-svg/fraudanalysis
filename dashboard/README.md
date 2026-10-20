# Financial Risk Analysis Dashboard - Streamlit UI

A production-ready Streamlit dashboard for monitoring fraud detection, analyzing transactions, managing alerts, and reviewing ML models. Integrates seamlessly with the FastAPI backend.

## Features

- **Authentication & Authorization**
  - JWT-based login with session management
  - Role-based access control (Admin, Analyst, Viewer)
  - Automatic session timeout (15 minutes, configurable)
  - Login attempt lockout protection

- **Dashboard Pages**
  1. **Executive Dashboard** - KPIs, fraud trends, risk distribution, top merchants
  2. **Transaction Explorer** - Search, filter, analyze individual transactions
  3. **Fraud Alerts** - Alert queue management with review workflow
  4. **Financial Risk Analytics** - Customer risk profiles, patterns, geographic analysis
  5. **Rule Management** - Create/edit fraud detection rules (admin only)
  6. **Model Performance** - ML model metrics, training history, feature importance
  7. **User Management** - User CRUD, role assignment (admin only)
  8. **Audit Logs** - Compliance and audit trail

- **Interactive Components**
  - Plotly charts for exploration and trend analysis
  - Filterable data tables with pagination
  - Real-time risk assessment and alerts
  - CSV/JSON export capabilities
  - Dark mode support

## Project Structure

```
dashboard/
├── app.py                 # Main entry point
├── config.py             # Configuration and constants
├── components/
│   ├── __init__.py
│   ├── auth_handler.py   # Authentication logic
│   ├── api_client.py     # Backend API communication
│   ├── charts.py         # Chart components
│   ├── filters.py        # Filter components
│   ├── tables.py         # Table components
│   └── utils.py          # Utility functions
├── pages/
│   ├── 00_Login.py       # Login page
│   ├── 01_Dashboard.py   # Executive dashboard
│   ├── 02_Transaction_Explorer.py
│   ├── 03_Fraud_Alerts.py
│   ├── 04_Financial_Risk_Analytics.py
│   ├── 05_Rule_Management.py
│   ├── 06_Model_Performance.py
│   ├── 07_User_Management.py
│   └── 08_Audit_Logs.py
└── README.md
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements-dashboard.txt
```

### 2. Configure Environment

Copy the template and update with your settings:

```bash
cp .env.dashboard.template .env.dashboard
```

Edit `.env.dashboard` with:
- `API_BASE_URL` - Your FastAPI backend URL
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- Session timeout and feature flags

### 3. Ensure Backend is Running

The FastAPI backend must be running on the configured API_BASE_URL:

```bash
python backend/main.py  # Or however your backend starts
# Backend should be available at http://localhost:8000
```

## Running the Dashboard

### Development Mode

```bash
streamlit run dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

### Production Mode

```bash
streamlit run dashboard/app.py \
  --logger.level=error \
  --client.showErrorDetails=false \
  --server.headless=true
```

## Configuration

### config.py

Central configuration file with:
- API settings (base URL, timeouts)
- Session management (timeout, max attempts)
- Role-based permissions
- Page definitions and metadata
- Color scheme and styling

### Environment Variables

See `.env.dashboard.template` for available settings:

- `API_BASE_URL` - Backend API endpoint
- `SESSION_TIMEOUT_MINUTES` - Session expiration time
- `MAX_LOGIN_ATTEMPTS` - Failed login threshold
- `ENABLE_*` - Feature flags for pages/features

## Authentication

### Login Flow

1. User enters email and password
2. AuthHandler calls `/auth/login` on backend
3. Backend returns JWT token if credentials valid
4. Token stored in `st.session_state`
5. Token injected in all subsequent API requests

### Session Management

- Session timeout enforced on every page load
- Automatic logout on timeout (15 minutes default)
- Manual logout button available
- Login attempt lockout after 5 failures (15 minutes)

### Role-Based Access

Three roles with permissions:
- **Admin** - Full access to all pages and features
- **Analyst** - Access to dashboards, alerts, analytics, audit logs
- **Viewer** - Read-only access to dashboards and reports

Permission checks happen on:
- Page load (page redirects to login if unauthorized)
- Component render (sensitive actions hidden)
- API calls (server enforces additional checks)

## API Integration

### APIClient

The `APIClient` class handles all backend communication:

```python
from dashboard.components import APIClient

client = APIClient(base_url="http://localhost:8000", token=token)

# Get transactions
transactions = client.get_transactions(
    customer_id=None,
    start_date=None,
    end_date=None,
    limit=100
)

# Create alert decision
decision = client.create_alert_decision(
    alert_id="alert-123",
    decision="approve",
    notes="Transaction legitimate"
)
```

### Error Handling

API errors are handled gracefully:
- 401 Unauthorized → User redirected to login
- 403 Forbidden → Error message shown
- 404 Not Found → Empty state displayed
- 5xx Server Errors → Retry with exponential backoff

## Component Architecture

### Charts (charts.py)

Reusable Plotly chart functions:
- `create_line_chart()` - Time series data
- `create_bar_chart()` - Category comparison
- `create_pie_chart()` - Composition analysis
- `create_histogram()` - Distribution analysis
- `create_heatmap()` - Geographic/matrix data
- `create_risk_distribution_chart()` - Risk levels

All accept flexible data format: `List[Dict[str, Any]]`

### Filters (filters.py)

Reusable filter components:
- `filter_date_range()` - Date selection
- `filter_amount_range()` - Currency range slider
- `filter_risk_level()` - Risk level selector
- `filter_status()` - Status filter
- `apply_filters_to_data()` - In-memory filtering

### Tables (tables.py)

Formatted table display:
- `create_transaction_table()` - Transaction listing
- `create_alert_table()` - Alert queue
- `create_rule_table()` - Fraud rules
- `create_user_table()` - User management
- `create_audit_log_table()` - Audit trail
- `create_paginated_table()` - Generic pagination

## Testing

### Manual Testing Checklist

- [ ] Login with valid credentials
- [ ] Login with invalid credentials (check lockout)
- [ ] Session timeout after 15 minutes
- [ ] Admin pages only show for admin users
- [ ] All charts render with mock data
- [ ] Filters work correctly
- [ ] Pagination works for large datasets
- [ ] CSV export downloads correctly
- [ ] API errors show friendly messages
- [ ] Logout clears session

### Integration Testing

Test with live backend:

```bash
# Terminal 1: Start backend
python backend/main.py

# Terminal 2: Start dashboard
streamlit run dashboard/app.py

# Terminal 3: Run tests
pytest tests/test_dashboard.py
```

### Mock Testing

Test without backend using mock data:

```python
# In test files
from dashboard.components import APIClient

# Mock API responses
mock_transactions = [
    {"id": "txn-001", "customer_id": "cust-1", "amount": 1000, "status": "approved"},
    # ... more data
]

# Use in tests
client.get_transactions = lambda: mock_transactions
```

## Performance Optimization

### Caching

Enable Redis caching for improved performance:

```python
# In config.py
CACHE_ENABLED = True
CACHE_TTL_SECONDS = 300
```

### Pagination

Large datasets are paginated (20 records per page default):
- Reduces memory usage
- Faster page loads
- Better UI responsiveness

### Lazy Loading

Charts and tables load data only when visible:
- Spinner displayed while loading
- Error handling if load fails

### Session State

Data cached in Streamlit session:
- Users, rules, models cached once per session
- Reduces redundant API calls
- Cache invalidated on logout

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-dashboard.txt .
RUN pip install -r requirements-dashboard.txt

COPY dashboard ./dashboard
COPY .env.dashboard .

CMD ["streamlit", "run", "dashboard/app.py"]
```

Build and run:

```bash
docker build -t fraud-dashboard .
docker run -p 8501:8501 fraud-dashboard
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-dashboard
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: dashboard
        image: fraud-dashboard:latest
        ports:
        - containerPort: 8501
        env:
        - name: API_BASE_URL
          value: http://api-service:8000
```

### Environment Variables for Deployment

```bash
# Production
ENVIRONMENT=production
DEBUG_MODE=false
HTTPS_ONLY=true
API_BASE_URL=https://api.example.com

# Security
JWT_SECRET_KEY=<production-secret-key>

# Session
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
```

## Security Considerations

### Authentication

- JWT tokens stored in session (not cookies)
- Tokens not persisted to disk
- 15-minute session timeout
- Login attempt lockout after 5 failures

### API Communication

- Token injected in Authorization header
- HTTPS recommended for production
- SSL certificate validation enabled
- 30-second request timeout

### Data Handling

- No sensitive data in logs
- Audit trail for all actions
- Role-based access to sensitive data
- XSS protection via Streamlit

### Best Practices

1. Use strong JWT secret key in production
2. Enable HTTPS for all connections
3. Use network policies to restrict API access
4. Monitor audit logs for suspicious activity
5. Regular security audits and updates

## Troubleshooting

### Common Issues

**"Connection refused" - Backend not running**
```bash
# Ensure backend is running
python backend/main.py

# Check API_BASE_URL in config
cat .env.dashboard | grep API_BASE_URL
```

**"Unauthorized" on login**
```
- Verify JWT_SECRET_KEY matches backend
- Check backend is using same secret
- Verify user exists and credentials correct
```

**"Charts not rendering"**
```
- Check data format (should be List[Dict])
- Verify required keys present in data
- Check browser console for JavaScript errors
```

**"Session timeout too frequent"**
```
- Adjust SESSION_TIMEOUT_MINUTES in config
- Check last_activity timestamp in logs
```

## Monitoring & Logging

### Logs Location

- **Application logs**: `dashboard.log`
- **Streamlit logs**: `~/.streamlit/logs/`
- **API call logs**: Included in audit trail

### Key Metrics to Monitor

- User login success/failure rate
- API response times
- Page load times
- Alert queue size
- Model training status

## Advanced Features

### Custom Styling

Modify CSS in `app.py`:

```python
st.markdown("""
    <style>
    .metric { color: #0066cc; }
    </style>
""", unsafe_allow_html=True)
```

### Extending Pages

Add new pages by creating `pages/NN_PageName.py`:

```python
import streamlit as st
from dashboard.components import APIClient, AuthHandler

def main():
    st.set_page_config(page_title="New Page")
    
    # Check authentication
    if not AuthHandler.is_authenticated():
        st.error("Please login first")
        return
    
    # Check permission
    if not AuthHandler.has_permission("new_page"):
        st.error("Access denied")
        return
    
    # Your page content
    st.title("New Page")
    # ...

if __name__ == "__main__":
    main()
```

### Adding New Components

Create reusable components in `components/`:

```python
# components/custom.py
def my_custom_component(data):
    """Reusable custom component."""
    # Implementation
    pass

# components/__init__.py
from .custom import my_custom_component
__all__ = [..., "my_custom_component"]
```

## API Documentation

See `backend/docs` for complete FastAPI documentation.

Key endpoints used by dashboard:
- `POST /auth/login` - User authentication
- `GET /transactions` - List transactions
- `GET /alerts` - Get fraud alerts
- `POST /alerts/{id}/review` - Review alert
- `GET /rules` - List fraud rules
- `POST /rules` - Create rule
- `GET /models` - List ML models
- `GET /users` - List users
- `GET /audit-logs` - Audit trail

## Contributing

When adding new features:

1. Create feature branch: `git checkout -b feature/new-feature`
2. Update components if adding new visualization type
3. Add permission checks if access restricted
4. Test with mock data first
5. Update this README
6. Submit pull request

## Support & Issues

For issues or questions:
1. Check troubleshooting section
2. Review logs in `dashboard.log`
3. Check backend API responses
4. File issue with debug logs attached

## License

Same as main project

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready
