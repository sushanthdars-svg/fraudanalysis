# Deployment Guide

## Financial Risk Analysis & Hybrid Fraud Detection System

This guide provides step-by-step instructions for deploying the Fraud Detection System to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.13 or 3.14
- **MySQL**: 8.0 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 1.29+ (for container orchestration)
- **Git**: 2.30+
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: Minimum 10GB

### Required Software

```bash
# Install Python 3.14 (Linux/macOS)
sudo apt-get install python3.14 python3.14-venv python3.14-dev

# Install MySQL 8.0 (Linux)
sudo apt-get install mysql-server mysql-client

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.14.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Local Deployment

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd "Financial Risk Analysis and Hybrid Fraud Detection System"
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3.14 -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your configuration
# Required variables:
#   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fraud_detection
#   SECRET_KEY=your-secret-key-here
#   DEBUG=false
```

### Step 5: Initialize Database

```bash
# Run migrations
python run_migrations.py upgrade

# Create admin user
python scripts/setup_admin.py

# Load sample data (optional, development only)
python scripts/reset_dev_database.py
```

### Step 6: Start Application

```bash
# Terminal 1: Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Streamlit dashboard
streamlit run dashboard/app.py
```

### Step 7: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready

# Access dashboard
# Open browser: http://localhost:8501
```

## Docker Deployment

### Step 1: Prerequisites

Ensure Docker and Docker Compose are installed:

```bash
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
git clone <repository-url>
cd "Financial Risk Analysis and Hybrid Fraud Detection System"
```

### Step 3: Configure Environment

```bash
# Create .env.docker file
cat > .env.docker << EOF
MYSQL_ROOT_PASSWORD=root_password_change_me
MYSQL_DATABASE=fraud_detection
MYSQL_USER=fraud_user
MYSQL_PASSWORD=fraud_password_change_me
SECRET_KEY=your-secret-key-change-in-production
DEBUG=false
ENVIRONMENT=production
EOF
```

### Step 4: Build Docker Images

**Option A: Using PowerShell script (Windows)**

```powershell
.\scripts\build_docker_images.ps1 -ImageTag "latest" -BuildVersion "1.0.0"
```

**Option B: Using Docker Compose**

```bash
docker-compose build --no-cache
```

### Step 5: Start Containers

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f dashboard
docker-compose logs -f mysql
```

### Step 6: Verify Services

```bash
# Check container status
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check dashboard
# Open browser: http://localhost:8501

# Access database
mysql -h localhost -u fraud_user -p fraud_detection
```

### Step 7: Create Admin User in Container

```bash
# Execute setup script in container
docker-compose exec api python scripts/setup_admin.py

# Or run with arguments
docker-compose exec api python scripts/setup_admin.py \
  --username admin \
  --email admin@example.com \
  --password your-strong-password
```

### Step 8: Stop Containers

```bash
# Stop all services
docker-compose down

# Remove volumes (warning: deletes data!)
docker-compose down -v
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (200+ tests)
- [ ] Security scan completed
- [ ] Database backed up
- [ ] SSL/TLS certificates configured
- [ ] Environment variables configured
- [ ] Monitoring and logging configured
- [ ] Backup and disaster recovery plan in place

### Step 1: Prepare Production Environment

```bash
# Create production configuration
cp .env.production .env

# Update with production values
vim .env

# Generate strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Database Migration

```bash
# Backup existing database
python scripts/backup_database.py

# Run migrations
python run_migrations.py upgrade

# Verify migration
python run_migrations.py current
```

### Step 3: Build and Push Docker Images

```bash
# Build images
docker-compose build --no-cache

# Tag images for registry
docker tag fraud-detection-api:latest myregistry.azurecr.io/fraud-detection-api:1.0.0
docker tag fraud-detection-dashboard:latest myregistry.azurecr.io/fraud-detection-dashboard:1.0.0

# Push to registry
docker push myregistry.azurecr.io/fraud-detection-api:1.0.0
docker push myregistry.azurecr.io/fraud-detection-dashboard:1.0.0
```

### Step 4: Deploy to Production

```bash
# Update docker-compose.yml with production registry
sed -i 's/fraud-detection-api:latest/myregistry.azurecr.io\/fraud-detection-api:1.0.0/g' docker-compose.yml

# Deploy
docker-compose -f docker-compose.yml up -d

# Verify
docker-compose ps
curl https://api.example.com/health
```

### Step 5: Post-Deployment Verification

```bash
# Check all services
docker-compose ps

# Verify API
curl https://api.example.com/health
curl https://api.example.com/health/ready
curl https://api.example.com/health/live

# Check logs for errors
docker-compose logs api
docker-compose logs dashboard

# Test basic workflows
# 1. Login to dashboard
# 2. Upload transactions
# 3. Verify fraud detection
# 4. Check alerts dashboard
```

## Environment Configuration

### Essential Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:password@host:3306/fraud_detection

# Security
SECRET_KEY=your-secret-key-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=https://api.example.com

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8501

# Environment
ENVIRONMENT=production
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=https://example.com,https://dashboard.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600
```

### Production Recommendations

```bash
# Security
SECRET_KEY=<generated-strong-key>
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Performance
MAX_POOL_SIZE=20
MIN_POOL_SIZE=5
POOL_RECYCLE=3600

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_ROTATION=daily
LOG_RETENTION=30

# Database
DATABASE_TIMEOUT=30
DATABASE_ECHO=false
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Cannot connect to database"

**Solutions:**
1. Verify MySQL is running: `mysql -u root -p -e "SELECT 1"`
2. Check DATABASE_URL in .env file
3. Verify MySQL credentials and permissions
4. Check firewall rules allow port 3306

#### Issue: "Port 8000 already in use"

**Solutions:**
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
# Or use different port
uvicorn app.main:app --port 8001
```

#### Issue: "Permission denied" on Docker

**Solutions:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Issue: "Migration failed"

**Solutions:**
1. Check database connection
2. Verify migration files exist
3. Check migration history: `python run_migrations.py history`
4. Rollback if needed: `python run_migrations.py downgrade`

#### Issue: "Out of memory"

**Solutions:**
1. Check memory usage: `free -h`
2. Increase MySQL max_connections limit
3. Optimize database queries
4. Increase swap space if needed

#### Issue: "Slow performance"

**Solutions:**
1. Check database indexes
2. Enable query logging: `SET global general_log = 1;`
3. Monitor with `EXPLAIN` plans
4. Scale horizontally with load balancer

### Checking Logs

```bash
# View application logs
tail -f logs/app.log

# View API specific logs
tail -f logs/api.log

# View database logs
docker-compose logs mysql

# View all logs
docker-compose logs -f
```

### Health Check Commands

```bash
# API health
curl http://localhost:8000/health

# API readiness
curl http://localhost:8000/health/ready

# API liveness
curl http://localhost:8000/health/live

# Database health
mysql -u user -p -e "SELECT 1"

# Redis health
redis-cli ping
```

## Monitoring and Logging

### Application Health Monitoring

Monitor these metrics regularly:
- API response time (target: <200ms)
- Error rate (target: <1%)
- Database connection pool usage
- Memory usage (target: <80%)
- Disk usage (target: <85%)

### Log Access

```bash
# Real-time application logs
docker-compose exec api tail -f /app/logs/app.log

# Search logs
docker-compose exec api grep "ERROR" /app/logs/app.log

# Export logs
docker-compose exec api tar czf logs.tar.gz /app/logs/
docker-compose cp api:/app/logs.tar.gz ./
```

## Backup and Recovery

### Backup Database

```bash
# Create backup
python scripts/backup_database.py

# Backup with custom retention
python scripts/backup_database.py --retention-days 30

# View backups
ls -lh backup/
```

### Restore Database

```bash
# List available backups
python scripts/backup_database.py --list

# Restore from backup
python scripts/backup_database.py --restore backup/fraud_detection_backup_2024-01-15_10-30-00.sql.gz
```

## Support and Escalation

For issues or questions:

1. Check logs: `docker-compose logs`
2. Review troubleshooting section above
3. Check application health: `/health` endpoint
4. Contact system administrator or support team

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
