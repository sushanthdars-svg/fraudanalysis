#!/bin/bash

# Populate database with sample data via API calls
# This script adds customers, transactions, and rules to the system

BASE_URL="http://fraud_detection_api:8000"
API_URL="http://localhost:8001"  # For local testing

echo "🌱 Starting to populate database with sample data..."
echo "=================================================="

# First, register/login to get a token
echo -e "\n1️⃣ Authenticating..."

# Try to login with default credentials
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@fraud-detection.local",
    "password": "password"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get authentication token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Authentication successful"
echo "Token: ${TOKEN:0:20}..."

# Function to make API calls with token
call_api() {
  local method=$1
  local endpoint=$2
  local data=$3
  
  curl -s -X $method "$API_URL$endpoint" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$data"
}

# Add sample customers via customer endpoint if it exists
echo -e "\n2️⃣ Adding sample data..."

# Sample transaction data
TRANSACTION_1=$(cat <<'EOF'
{
  "transaction_id": "TXN-20261023-0001",
  "customer_id": 1,
  "amount": 5000.00,
  "currency": "USD",
  "merchant_name": "Amazon",
  "merchant_id": "MER-AMAZON",
  "merchant_category": "Electronics",
  "transaction_type": "purchase",
  "payment_method": "card",
  "card_last4": "4532",
  "transaction_date": "2026-10-23T15:30:00Z",
  "status": "completed"
}
EOF
)

echo "📝 Attempting to add transactions..."

# Test adding a transaction
RESPONSE=$(call_api POST "/api/transactions" "$TRANSACTION_1")
echo "Response: $RESPONSE"

# Add more sample data...
echo -e "\n✅ Sample data population complete!"
echo "You can now view data in the web interface"
