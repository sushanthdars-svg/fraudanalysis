#!/bin/bash
# Dashboard startup script

set -e

echo "=== Fraud Detection Dashboard ==="
echo ""

# Check if .env.dashboard exists
if [ ! -f .env.dashboard ]; then
    echo "⚠️  .env.dashboard not found"
    echo "Creating from template..."
    cp .env.dashboard.template .env.dashboard
    echo "✓ Created .env.dashboard - please edit with your settings"
    echo ""
fi

# Load environment
export $(cat .env.dashboard | grep -v '^#' | xargs)

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if requirements are installed
echo "Checking dependencies..."
python3 -m pip list | grep -q streamlit || {
    echo "❌ Dependencies not installed"
    echo "Run: pip install -r requirements-dashboard.txt"
    exit 1
}

echo "✓ Dependencies installed"
echo ""

# Check if backend is accessible
echo "Checking backend connectivity..."
if ! timeout 2 python3 -c "import requests; requests.get('$API_BASE_URL/health', timeout=1)" 2>/dev/null; then
    echo "⚠️  Warning: Backend at $API_BASE_URL is not responding"
    echo "   Ensure FastAPI backend is running before using the dashboard"
    echo ""
fi

echo "Starting dashboard..."
echo "Dashboard will be available at: http://localhost:8501"
echo ""
echo "To stop the dashboard, press Ctrl+C"
echo ""

# Start Streamlit
streamlit run dashboard/app.py --logger.level=info
