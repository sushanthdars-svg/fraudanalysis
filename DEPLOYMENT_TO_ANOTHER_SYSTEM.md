# Deployment Guide: Financial Risk Analysis & Hybrid Fraud Detection System

## Overview
This comprehensive guide explains how to deploy the complete Financial Risk Analysis and Hybrid Fraud Detection System to another system (Linux, macOS, or Windows).

**Application Stack:**
- **Backend**: FastAPI (Python 3.14)
- **Database**: MySQL 8.0
- **Cache**: Redis 7
- **Frontend**: Streamlit Dashboard
- **Architecture**: Containerized (Docker/Docker Compose)

---

## Option 1: Docker Compose Deployment (Recommended)

### Prerequisites
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Docker Compose (v2.0+)
- Git

### Step 1: Clone the Repository

```bash
git clone <your-repository-url> financial-fraud-detection
cd financial-fraud-detection
```

### Step 2: Configure Environment Variables

The application uses `.env` files for configuration. Copy the template:

```bash
cp .env.example .env
```

Edit `.env` with your specific settings:

```env
# Database Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_DATABASE=fraud_detection
MYSQL_USER=fraud_user
MYSQL_PASSWORD=your_secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=mysql+pymysql://fraud_user:your_secure_password@mysql:3306/fraud_detection

# Authentication
SECRET_KEY=your_super_secret_key_change_this

# Environment
ENVIRONMENT=production
DEBUG=False

# Optional Services
REDIS_URL=redis://redis:6379/0
```

**Important Security Notes:**
- Never commit `.env` files with real credentials
- Use strong, unique passwords
- Use a cryptographic key generator for `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

### Step 3: Start the Application

```bash
# Build and start all services (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f mysql
docker-compose logs -f dashboard
```

### Step 4: Verify Services

```bash
# Check service status
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Access Dashboard
# Open browser: http://localhost:8501

# Access MySQL
mysql -h 127.0.0.1 -P 3307 -u fraud_user -p
```

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose exec api python run_migrations.py

# Seed sample data
docker-compose exec api python seed_database.py
```

### Step 6: Stop the Application

```bash
# Graceful shutdown
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Option 2: Native Installation (Without Docker)

### Prerequisites
- Python 3.14+
- MySQL 8.0
- Redis 7.0 (optional)
- Git

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.14 python3.14-venv python3-dev \
    mysql-server redis-server git build-essential libmysqlclient-dev
```

**macOS (using Homebrew):**
```bash
brew install python@3.14 mysql redis git
brew services start mysql
brew services start redis
```

**Windows (PowerShell):**
```powershell
# Install via Chocolatey or Windows package managers
choco install python mysql redis-64 git

# Or download and install manually from:
# - Python: https://python.org
# - MySQL: https://mysql.com/downloads
# - Redis: https://github.com/microsoftarchive/redis/releases
```

### Step 2: Clone Repository

```bash
git clone <your-repository-url> financial-fraud-detection
cd financial-fraud-detection
```

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment
python3.14 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat
```

### Step 4: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dashboard.txt
```

### Step 5: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Key settings for native installation:**
```env
DATABASE_URL=mysql+pymysql://fraud_user:password@localhost:3306/fraud_detection
REDIS_URL=redis://localhost:6379/0
API_HOST=127.0.0.1
API_PORT=8000
```

### Step 6: Initialize Database

```bash
# Create database and run migrations
python run_migrations.py

# Seed sample data
python seed_database.py
```

### Step 7: Start Services

**Terminal 1: Run API Server**
```bash
python run.py
# API will be available at http://localhost:8000
```

**Terminal 2: Run Dashboard**
```bash
streamlit run dashboard/app.py --server.port=8501
# Dashboard will be available at http://localhost:8501
```

---

## Option 3: Cloud Deployment

### AWS Deployment

**ECS (Elastic Container Service):**
```bash
# 1. Push Docker images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag fraud-detection-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/fraud-detection-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/fraud-detection-api:latest

# 2. Create ECS task definition, service, and load balancer
# 3. Configure RDS MySQL and ElastiCache Redis
```

**Using AWS CloudFormation (Infrastructure as Code):**
See: `DEPLOYMENT_INFRASTRUCTURE.md`

### Azure Deployment

**Azure Container Instances (ACI):**
```bash
# Login to Azure
az login

# Create resource group
az group create --name fraud-detection-rg --location eastus

# Deploy using Docker Compose
az container create \
  --resource-group fraud-detection-rg \
  --name fraud-detection \
  --image group.azurecr.io/fraud-detection-api:latest \
  --environment-variables \
    MYSQL_HOST=fraud-db.mysql.database.azure.com \
    MYSQL_USER=fraud_user \
  --ports 8000 8501
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/dashboard-deployment.yaml
kubectl apply -f k8s/services.yaml
```

---

## Post-Deployment Configuration

### Database Setup

1. **Run Migrations**
   ```bash
   # Using Docker Compose
   docker-compose exec api python run_migrations.py
   
   # Or native installation
   python run_migrations.py
   ```

2. **Load Sample Data**
   ```bash
   # Using Docker Compose
   docker-compose exec api python seed_database.py
   
   # Or native installation
   python seed_database.py
   ```

### Health Checks

```bash
# API Health
curl -X GET http://localhost:8000/health

# Database Connection
curl -X GET http://localhost:8000/api/v1/health/db

# Full System Status
curl -X GET http://localhost:8000/api/v1/health/system
```

### Monitoring & Logging

**View Logs:**
```bash
# Docker Compose
docker-compose logs -f --tail=100

# Native installation
tail -f logs/api.log
tail -f logs/dashboard.log
```

**Access Monitoring Dashboard:**
```
http://localhost:8501/monitoring
```

---

## Backup & Recovery

### Docker Compose Backup

```bash
# Backup database
docker-compose exec mysql mysqldump -u fraud_user -p fraud_detection > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup volumes
docker run --rm -v fraud_detection_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
docker cp fraud_detection_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Restore from Backup

```bash
# Restore database
docker-compose exec -T mysql mysql -u fraud_user -p fraud_detection < backup_20240101_120000.sql

# Restore Redis
docker cp redis_backup_20240101_120000.rdb fraud_detection_redis:/data/dump.rdb
docker-compose restart redis
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Refused**
```bash
# Check MySQL is running
docker-compose ps mysql

# Check database credentials in .env
# Verify database host is correct (use 'mysql' as hostname in Docker)
```

**2. Port Already in Use**
```bash
# Check what's using the port
# Linux/macOS:
lsof -i :8000
lsof -i :3306

# Windows (PowerShell):
Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property State, OwningProcess
```

**3. Out of Memory**
```bash
# Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory: increase to 4GB+

# Or modify docker-compose.yml:
services:
  api:
    mem_limit: 2g
```

**4. Slow Performance**
- Increase MySQL buffer pool: `innodb_buffer_pool_size=2G`
- Add Redis cache configuration
- Enable query optimization
- Check database indexes

**5. SSL/TLS Certificate Issues**
```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update docker-compose.yml to use SSL
```

---

## Production Checklist

Before deploying to production, verify:

- [ ] Environment variables are configured with production values
- [ ] Passwords are strong (16+ characters, mixed case, numbers, symbols)
- [ ] Database backups are configured
- [ ] SSL/TLS certificates are valid
- [ ] Firewall rules are properly configured
- [ ] API authentication is enforced
- [ ] Rate limiting is enabled
- [ ] Logging and monitoring are active
- [ ] Database indexes are optimized
- [ ] Memory and CPU limits are appropriate
- [ ] Health checks are passing
- [ ] Backup restoration has been tested

---

## Performance Tuning

### MySQL Optimization
```sql
-- Increase buffer pool
SET GLOBAL innodb_buffer_pool_size = 2147483648;

-- Create indexes for frequently queried columns
CREATE INDEX idx_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_user_id ON transactions(user_id);
CREATE INDEX idx_fraud_flag ON transactions(fraud_flag);
```

### API Configuration
```python
# In fastapi configuration
app.state.db_pool_size = 20
app.state.db_max_overflow = 40
app.state.cache_ttl = 3600
```

### Redis Caching
```bash
# Monitor Redis performance
docker-compose exec redis redis-cli INFO stats

# Set memory management policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## Upgrading the Application

### Update Code
```bash
# Pull latest changes
git pull origin main

# Update Python dependencies
pip install -r requirements.txt --upgrade

# Rebuild Docker images
docker-compose build --no-cache
```

### Database Schema Updates
```bash
# Run new migrations
python run_migrations.py

# Verify schema changes
docker-compose exec mysql mysql -u fraud_user -p -e "SHOW TABLES;"
```

### Zero-Downtime Deployment (Docker)
```bash
# Update specific service
docker-compose up -d --no-deps --build api

# Health check before proceeding
curl http://localhost:8000/health
```

---

## Security Considerations

1. **Never commit credentials** to version control
2. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)
3. **Enable SSL/TLS** for all communications
4. **Implement rate limiting** on API endpoints
5. **Use strong database passwords** (stored in secrets manager)
6. **Enable database encryption** at rest
7. **Implement proper access controls** and RBAC
8. **Regular security audits** of dependencies
9. **Keep Docker images updated** with latest patches
10. **Monitor logs** for suspicious activities

---

## Support Resources

- **Documentation**: See `DEPLOYMENT_GUIDE.md`, `OPERATIONS_RUNBOOK.md`
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Test Guide**: `COMPREHENSIVE_TEST_GUIDE.md`
- **Architecture**: See `DEPLOYMENT_INFRASTRUCTURE.md`

---

## Quick Reference Commands

```bash
# Docker Compose
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f            # View logs
docker-compose ps                 # Check status
docker-compose exec api bash      # Access container

# MySQL
mysql -h localhost -u fraud_user -p fraud_detection    # Connect to database
mysqldump -u fraud_user -p fraud_detection > backup.sql # Backup

# Python (Native Installation)
python run.py                      # Start API
python seed_database.py            # Seed data
python run_migrations.py           # Run migrations

# Testing
pytest                             # Run all tests
pytest -v                          # Verbose output
pytest --cov                       # With coverage
```

---

**Last Updated**: October 2024
**Application Version**: 1.0.0
**Python Version**: 3.14
**Status**: ✅ Production Ready
