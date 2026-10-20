# Dashboard Testing Guide

## Overview

This guide provides comprehensive instructions for testing the Streamlit dashboard with various scenarios and configurations.

## Prerequisites

1. **Python 3.8+** installed
2. **FastAPI Backend** running (see backend README)
3. **Dashboard Dependencies** installed:
   ```bash
   pip install -r requirements-dashboard.txt
   ```

## Test Environment Setup

### 1. Backend Setup

Ensure the FastAPI backend is running:

```bash
# Terminal 1: Start backend
cd backend
python main.py
# Should show: Uvicorn running on http://127.0.0.1:8000
```

### 2. Configure Dashboard

```bash
# Copy and edit configuration
cp .env.dashboard.template .env.dashboard

# Edit .env.dashboard with:
API_BASE_URL=http://localhost:8000
SESSION_TIMEOUT_MINUTES=15
DEBUG_MODE=true
```

### 3. Start Dashboard

```bash
# Terminal 2: Start dashboard
streamlit run dashboard/app.py
# Should show: You can now view your Streamlit app in your browser
```

## Test Scenarios

### A. Authentication Testing

#### Test A1: Valid Login
**Steps:**
1. Navigate to http://localhost:8501
2. Enter valid email (e.g., `admin@example.com`)
3. Enter valid password (e.g., `password123`)
4. Click "Login"

**Expected Results:**
- Dashboard loads successfully
- User name displayed in sidebar
- Pages available based on role

**Pass/Fail:** ___

#### Test A2: Invalid Credentials
**Steps:**
1. Enter invalid email or password
2. Click "Login"

**Expected Results:**
- Error message shown: "Invalid email or password"
- User stays on login page
- No session created

**Pass/Fail:** ___

#### Test A3: Login Attempt Lockout
**Steps:**
1. Enter wrong password 5 times
2. Attempt 6th login immediately

**Expected Results:**
- After 5th failure: "Account locked. Try again after 15 minutes."
- 6th attempt blocked with same message
- Cannot login for 15 minutes

**Pass/Fail:** ___

#### Test A4: Session Timeout
**Steps:**
1. Login successfully
2. Navigate to a page
3. Wait 15 minutes (or adjust timeout in .env for testing)
4. Interact with page (click button, scroll)

**Expected Results:**
- Page shows: "Session expired. Please login again."
- Redirected to login page
- Session state cleared

**Pass/Fail:** ___

#### Test A5: Logout
**Steps:**
1. Login successfully
2. Click "Logout" in sidebar
3. Try to access dashboard pages

**Expected Results:**
- Redirected to login page
- Session cleared
- Cannot access pages without re-login

**Pass/Fail:** ___

### B. Role-Based Access Testing

#### Test B1: Admin Role Access
**Steps:**
1. Login as admin user
2. Check sidebar navigation

**Expected Results:**
- All 8 pages visible
- Rule Management page accessible
- User Management page accessible
- Audit Logs page accessible

**Pass/Fail:** ___

#### Test B2: Analyst Role Access
**Steps:**
1. Login as analyst user
2. Check sidebar navigation

**Expected Results:**
- Dashboard, Transaction Explorer, Fraud Alerts visible
- Financial Risk Analytics visible
- Model Performance visible
- Rule Management NOT visible
- User Management NOT visible

**Pass/Fail:** ___

#### Test B3: Viewer Role Access
**Steps:**
1. Login as viewer user
2. Check sidebar navigation

**Expected Results:**
- Dashboard visible (read-only)
- Transaction Explorer visible (read-only)
- All other pages NOT visible or read-only
- Cannot modify data

**Pass/Fail:** ___

#### Test B4: Unauthorized Page Access
**Steps:**
1. Login as non-admin
2. Try to directly access admin page URL
3. Modify URL to access restricted page

**Expected Results:**
- Access denied message shown
- Redirected to dashboard
- No data displayed

**Pass/Fail:** ___

### C. Dashboard Pages Testing

#### Test C1: Executive Dashboard (Page 01)
**Steps:**
1. Navigate to Dashboard
2. Observe KPI cards
3. Scroll through charts
4. Check data freshness

**Expected Results:**
- 4 KPI cards load (Transactions, Fraud Rate, Alerts, Risk Score)
- Fraud trends chart displays (last 30 days)
- Top merchants chart displays
- Risk distribution pie chart displays
- All data visible and properly formatted
- Charts interactive (hover shows details)

**Pass/Fail:** ___

#### Test C2: Transaction Explorer (Page 02)
**Steps:**
1. Navigate to Transaction Explorer
2. Use search box to find transaction
3. Apply filters (date range, amount, merchant)
4. View transaction detail
5. Export to CSV

**Expected Results:**
- Transactions load in table
- Search works correctly
- Filters apply data accurately
- Pagination works (20 per page)
- Detail view shows all transaction info
- CSV export downloads successfully

**Pass/Fail:** ___

#### Test C3: Fraud Alerts (Page 03)
**Steps:**
1. Navigate to Fraud Alerts
2. Filter by status (pending, reviewing, resolved)
3. Click alert to view details
4. Add notes to alert
5. Make decision (approve/reject)
6. Check audit trail

**Expected Results:**
- Alert queue displays with status
- Filters work correctly
- Detail panel shows alert info and triggered rules
- Can add notes (if analyst+)
- Can make decision (if analyst+)
- Decision recorded in audit trail
- Status changes reflect in table

**Pass/Fail:** ___

#### Test C4: Financial Risk Analytics (Page 04)
**Steps:**
1. Navigate to Risk Analytics
2. View customer risk profiles
3. Check transaction patterns
4. View geographic heatmap
5. Scroll through all sections

**Expected Results:**
- Customer risk profiles show average amount, frequency, pattern
- Transaction amount distribution displayed
- Time-of-day analysis shown
- Merchant category analysis displayed
- Geographic heatmap displays properly
- All charts interactive
- No loading errors

**Pass/Fail:** ___

#### Test C5: Rule Management (Page 05) - Admin Only
**Steps:**
1. Login as admin
2. Navigate to Rule Management
3. View list of rules
4. Create new rule
5. Edit existing rule
6. View rule performance
7. Disable/enable rule

**Expected Results:**
- All rules (R01-R10) displayed
- Can create new rule with form
- Can edit threshold and weight
- Rule performance metrics shown
- Can toggle enable/disable
- Changes persisted to backend

**Pass/Fail:** ___

#### Test C6: Model Performance (Page 06)
**Steps:**
1. Navigate to Model Performance
2. View model metrics (precision, recall, F1)
3. Check training history
4. View feature importance chart
5. Compare different models

**Expected Results:**
- Model metrics display correctly
- Confusion matrix shown
- Training history table displays
- Feature importance chart shows top features
- Model selector works
- Metrics update when model changed

**Pass/Fail:** ___

#### Test C7: User Management (Page 07) - Admin Only
**Steps:**
1. Login as admin
2. Navigate to User Management
3. View all users
4. Create new user
5. Edit user role
6. Deactivate/activate user
7. View activity log

**Expected Results:**
- User list displays with details
- Can create new user with form
- Can change user roles
- Can toggle active status
- Activity log shows user actions
- Changes saved to backend

**Pass/Fail:** ___

#### Test C8: Audit Logs (Page 08)
**Steps:**
1. Navigate to Audit Logs
2. Filter by actor, action, date range
3. View detailed event info
4. Export audit trail (CSV/JSON)
5. Generate compliance report

**Expected Results:**
- Audit events display with timestamp
- Filters work correctly
- Detail view shows complete event info
- CSV export downloads
- JSON export downloads
- Compliance report generated

**Pass/Fail:** ___

### D. Component Testing

#### Test D1: Charts Rendering
**Steps:**
1. Navigate through pages with charts
2. Hover over chart elements
3. Check tooltips display correctly

**Expected Results:**
- All charts render without errors
- Interactive tooltips show data
- Charts responsive to window resize
- Legends display correctly

**Pass/Fail:** ___

#### Test D2: Filters Functionality
**Steps:**
1. Use date range filter
2. Use amount range slider
3. Use dropdown filters
4. Apply multiple filters
5. Clear filters

**Expected Results:**
- Date filter returns correct date range
- Amount slider works (min/max)
- Dropdowns select correctly
- Multiple filters combine (AND logic)
- Clear button resets all filters

**Pass/Fail:** ___

#### Test D3: Table Pagination
**Steps:**
1. View table with >20 records
2. Click page number
3. Check record count
4. Navigate through pages

**Expected Results:**
- Pagination controls visible
- Page navigation works
- Records change per page
- Record count shows correctly
- Can go back to previous page

**Pass/Fail:** ___

#### Test D4: Data Export
**Steps:**
1. Use CSV export button
2. Open exported file
3. Verify data accuracy
4. Check formatting

**Expected Results:**
- CSV file downloads
- File opens in Excel/text editor
- All columns present
- Data matches table display
- Formatting correct

**Pass/Fail:** ___

### E. Error Handling Testing

#### Test E1: Backend Unavailable
**Steps:**
1. Stop FastAPI backend
2. Try to login
3. Try to navigate to dashboard pages
4. Restart backend

**Expected Results:**
- Login shows error: "Could not connect to server"
- Pages show loading spinner initially
- Error message after timeout
- Works again when backend restarted

**Pass/Fail:** ___

#### Test E2: API Error Responses
**Steps:**
1. Trigger 404 error (invalid ID)
2. Trigger 403 error (permission denied)
3. Trigger 500 error (server error)

**Expected Results:**
- 404 shows "Resource not found"
- 403 shows "Access denied"
- 500 shows "Server error, try again later"
- User stays on current page

**Pass/Fail:** ___

#### Test E3: Invalid Data Format
**Steps:**
1. Manually send malformed request
2. View error handling

**Expected Results:**
- Invalid data handled gracefully
- Error message shown to user
- No crashes or console errors

**Pass/Fail:** ___

#### Test E4: Network Timeout
**Steps:**
1. Make slow backend response (add delay)
2. Try to load data
3. Verify timeout behavior

**Expected Results:**
- After 30s timeout, error shown
- User can retry
- No application freeze

**Pass/Fail:** ___

### F. Security Testing

#### Test F1: XSS Protection
**Steps:**
1. Try to inject JS in search box: `<script>alert('xss')</script>`
2. Submit form
3. Check if alert appears

**Expected Results:**
- Script not executed
- Text displayed as-is (escaped)
- No alert shown

**Pass/Fail:** ___

#### Test F2: SQL Injection Prevention
**Steps:**
1. Try SQL injection in filters: `' OR '1'='1`
2. Submit search
3. Observe behavior

**Expected Results:**
- Query treated as string literal
- No unexpected results
- Backend safely handles injection attempt

**Pass/Fail:** ___

#### Test F3: Token Security
**Steps:**
1. Open browser dev tools
2. Check localStorage/sessionStorage
3. Verify token not stored in plain text

**Expected Results:**
- Token in session state (Streamlit manages)
- No token in localStorage
- No sensitive data in cookies

**Pass/Fail:** ___

#### Test F4: Role Bypass Attempts
**Steps:**
1. As viewer, try to modify data
2. Try to access admin-only pages
3. Try to change role (edit POST request)

**Expected Results:**
- Modify operations blocked by permissions
- Admin pages show access denied
- Role cannot be changed by user
- Backend enforces permissions

**Pass/Fail:** ___

### G. Performance Testing

#### Test G1: Large Dataset Handling
**Steps:**
1. Request transaction list (10,000+ records)
2. Check pagination works
3. Export large dataset

**Expected Results:**
- Pagination prevents loading all records
- Page loads within 3 seconds
- CSV export completes within 10s

**Pass/Fail:** ___

#### Test G2: Chart Performance
**Steps:**
1. Load page with multiple charts
2. Check rendering time
3. Interact with charts

**Expected Results:**
- Page loads within 5 seconds
- Charts render within 2 seconds
- Hover/zoom interactions smooth

**Pass/Fail:** ___

#### Test G3: Session State Caching
**Steps:**
1. Load Dashboard
2. Navigate to Transaction Explorer
3. Navigate back to Dashboard
4. Check if data reloaded or cached

**Expected Results:**
- Second view faster than first
- Cached data used when available
- Manual refresh still works

**Pass/Fail:** ___

## Test Automation

### Pytest Integration Testing

Create `tests/test_dashboard.py`:

```python
import pytest
from dashboard.components import APIClient, AuthHandler
from dashboard.config import ROLE_PERMISSIONS

def test_login_success():
    """Test successful login."""
    result = APIClient.login("admin@example.com", "password123")
    assert result["token"] is not None
    assert result["user"]["role"] == "admin"

def test_login_failure():
    """Test failed login."""
    result = APIClient.login("admin@example.com", "wrong_password")
    assert result["token"] is None
    assert "error" in result

def test_admin_permission():
    """Test admin permissions."""
    assert AuthHandler.has_permission("rule_management", "admin")
    assert AuthHandler.has_permission("user_management", "admin")

def test_viewer_permission():
    """Test viewer permissions."""
    assert not AuthHandler.has_permission("rule_management", "viewer")
    assert AuthHandler.has_permission("dashboard", "viewer")
```

Run tests:

```bash
pytest tests/test_dashboard.py -v
```

## Test Results Summary

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| A1 | Valid Login | _____ | |
| A2 | Invalid Credentials | _____ | |
| A3 | Login Lockout | _____ | |
| A4 | Session Timeout | _____ | |
| A5 | Logout | _____ | |
| B1 | Admin Access | _____ | |
| B2 | Analyst Access | _____ | |
| B3 | Viewer Access | _____ | |
| B4 | Unauthorized Access | _____ | |
| C1 | Executive Dashboard | _____ | |
| C2 | Transaction Explorer | _____ | |
| C3 | Fraud Alerts | _____ | |
| C4 | Risk Analytics | _____ | |
| C5 | Rule Management | _____ | |
| C6 | Model Performance | _____ | |
| C7 | User Management | _____ | |
| C8 | Audit Logs | _____ | |
| D1 | Charts Rendering | _____ | |
| D2 | Filters | _____ | |
| D3 | Pagination | _____ | |
| D4 | Data Export | _____ | |
| E1 | Backend Unavailable | _____ | |
| E2 | API Errors | _____ | |
| E3 | Invalid Data | _____ | |
| E4 | Network Timeout | _____ | |
| F1 | XSS Protection | _____ | |
| F2 | SQL Injection | _____ | |
| F3 | Token Security | _____ | |
| F4 | Role Bypass | _____ | |
| G1 | Large Datasets | _____ | |
| G2 | Chart Performance | _____ | |
| G3 | Session Caching | _____ | |

## Performance Baselines

Expected performance metrics:

- **Page Load Time**: < 3 seconds
- **Chart Render Time**: < 2 seconds
- **API Response Time**: < 1 second (average)
- **Export Time**: < 10 seconds (1000+ records)
- **Session Initialization**: < 500ms

## Regression Testing

When changes are made:

1. Run all tests in sections A (Auth) and B (Access)
2. Run tests for modified pages (section C)
3. Run security tests (section F)
4. Run performance tests (section G)
5. Document results

## Bug Reporting Template

When issues found, document:

```
TEST ID: [e.g., C3]
TITLE: [Brief description]
SEVERITY: [Critical/High/Medium/Low]
STEPS TO REPRODUCE:
1. [Step 1]
2. [Step 2]
3. [Step 3]

EXPECTED RESULT:
[What should happen]

ACTUAL RESULT:
[What happened instead]

SCREENSHOT/LOGS:
[Attach if applicable]

ENVIRONMENT:
- Python version: [e.g., 3.11]
- Streamlit version: [e.g., 1.28.1]
- Backend: [Running/Stopped]
- OS: [Windows/Mac/Linux]
```

## Sign-Off

- **Tested By**: ____________
- **Date**: ____________
- **Total Tests**: 32
- **Passed**: _____
- **Failed**: _____
- **Blocked**: _____
- **Overall Status**: [PASS/FAIL]

---

**Note**: Update test cases as dashboard features evolve. Keep this guide current for quality assurance.
