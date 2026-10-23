#!/bin/bash
set -e

echo "=========================================="
echo "Waiting for database to be ready..."
echo "=========================================="
sleep 5

echo "=========================================="
echo "Seeding database with sample data..."
echo "=========================================="
python /app/seed_simple.py || echo "Database seeding skipped (already exists or error)"

echo "=========================================="
echo "Starting FastAPI application..."
echo "=========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
