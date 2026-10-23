# Foresight risk console

React + TypeScript frontend for the existing FastAPI service. The console uses a
responsive navy/emerald design, Lucide icons, Recharts, and custom CSS without
external font or UI services. Streamlit remains available during the transition.

## Run with Docker

From the repository root:

```powershell
docker compose up -d --build api dashboard frontend
```

- React: http://localhost:3000
- Existing Streamlit dashboard: http://localhost:8502
- API: http://localhost:8001

Use your existing account. Public registration creates a **viewer**, not an
administrator. Only an administrator can grant analyst/admin access.
`FRONTEND_HOST_PORT` can override the React port.

The frontend container proxies `/backend/` to the API. The API's model directory
is bind-mounted to the repository's `models` directory, so training artifacts
survive container recreation. Do not delete that directory when redeploying.

## Local frontend development

Requires Node.js 20.19+ or 22.12+ and a running API.

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. The development proxy targets
http://127.0.0.1:8001 by default (the project's Docker API, **not** port 8000).
Override `API_PROXY_TARGET` in the shell to use a different backend:

```powershell
$env:API_PROXY_TARGET = "http://127.0.0.1:8001"
npm.cmd run dev
```

## Model training

1. Sign in as an active **admin or analyst**.
2. Open **Model studio > Train a model**.
3. Choose labeled database transactions or synthetic demonstration data.
4. Select Random Forest, Logistic Regression, and/or Isolation Forest.
5. Set a sample limit from 100 to 5,000 and start training.

Training is a synchronous request with a visible busy state and a five-minute
budget; keep the page open. A cross-process filesystem lock prevents overlapping
runs across API workers sharing the model directory. If a connection is lost,
refresh the registry before retrying: the server may still have completed the run.

The database option selects the latest labeled transactions (up to the limit).
At least 100 labeled samples are needed. The chronological 70/10/20 splits must
each contain legitimate and fraudulent examples, and the training split needs at
least five of each for cross-validation.

Synthetic data is generated **in memory** and never inserted into the database.
Its metrics are clearly marked as demonstration results, not real-world evidence.
Every run saves a classifier (`.joblib`), fitted scaler (`.scaler`), and matching
JSON metadata containing feature names, source, and validation metrics. Metrics,
training history, feature importance (where supported), confusion matrix, and
cross-run comparison use this saved metadata; unavailable values are not invented.

**Training is not deployment.** UI-trained models are evaluation-only and excluded
from automatic live-model selection. The existing feature pipeline includes
whole-dataset customer aggregates, so independent evaluation and temporal-leakage
review are required before production use. Deploying a new scoring model is a
separate workflow.

API contract:

```http
POST /api/models/train
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "algorithms": ["random_forest", "logistic_regression"],
  "source": "database",
  "sample_limit": 1000
}
```

Returns `201` with `items`, `data_split`, and `total_samples`; `403` for insufficient
permissions, `409` for overlapping runs, and `422` for invalid configuration/data.
Saved metadata is available through `GET /api/models` and
`GET /api/models/{model_id}/metrics`.

## Implemented views and migration scope

- Overview: transaction statistics, risk distribution, activity chart, review links.
- Transactions: ID/customer/date/risk filters, pagination, details, current-page CSV.
- Risk analytics: date ranges, risk distribution, customer profiles and anomaly signals.
- Model studio: training, metrics, feature importance, history and comparison.
- Fraud alerts: status queues, evidence detail, documented review decisions.
- Detection rules: existing rule enable/disable and threshold/weight/severity editing.
- Team members: create users, assign roles, activate/deactivate accounts.
- Audit trail: actor/action/date filters, pagination and current-page CSV.

Navigation and direct links respect roles. JWTs are kept in browser session
storage, verified on reload, and cleared on sign-out or API `401`. Each tab has an
independent browser session. API errors are displayed with retry actions.

This is a parallel replacement, **not a declaration of full legacy feature parity**.
Advanced Streamlit workflows such as transaction CSV import, rule creation/deletion,
user deletion and compliance-report generation remain in the legacy dashboard.
Do not retire Streamlit until those workflows are migrated and accepted.

## Validation

```powershell
npm.cmd run build
npx.cmd playwright install chromium
```

The browser suite launches the actual FastAPI application and trains actual models
against an **isolated MySQL database**, not mocked API responses. It covers login,
reload/logout/expiry, registration, viewer restrictions, mobile navigation,
synthetic/database training, persisted metrics, transaction details, rule changes,
team roles, and alert decisions.

Start a dedicated disposable test database (do not reuse an application database):

```powershell
docker run --name fraud_detection_e2e_mysql --publish 127.0.0.1:3308:3306 --env MYSQL_ROOT_PASSWORD=browser-tests-only --env MYSQL_DATABASE=fraud_detection_e2e -d mysql:8.0-debian
# Wait until MySQL is ready, then:
$env:E2E_DATABASE_URL = "mysql+pymysql://root:browser-tests-only@127.0.0.1:3308/fraud_detection_e2e"
npm.cmd test
# Clean up only the dedicated test container:
docker rm -f -v fraud_detection_e2e_mysql
```

The backend Python dependencies must be installed. The suite requires free ports
5173 and 8765 and **recreates all tables in `fraud_detection_e2e`**. The server
refuses other database names. Test accounts and generated artifacts are isolated
from the normal app. Playwright starts/stops its API and Vite subprocesses.

Backend regression coverage (from the repository root):

```powershell
python -m pytest tests\test_model_training.py tests\test_model_performance.py tests\test_dashboard_navigation.py tests\test_ml.py tests\test_security.py tests\test_auth_registration.py tests\test_analytics_transactions.py tests\test_analytics_customers.py tests\test_analytics_api.py -q
```
