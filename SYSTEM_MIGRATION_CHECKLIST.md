# System Migration & Deployment Checklist

## Pre-Migration Planning

### 1. Source System Assessment
- [ ] Document current application version
- [ ] List all installed dependencies and their versions
- [ ] Document database schema and size
- [ ] Note any custom configurations or modifications
- [ ] Identify all external integrations and APIs
- [ ] List current environment variables and their values
- [ ] Document any SSL certificates or security keys
- [ ] Record current backup strategy

**Checklist Item:**
```bash
# Run on source system to capture current state
docker-compose ps
docker-compose images
docker-compose logs --tail=50 > deployment_logs.txt
docker-compose exec mysql mysqldump --all-databases > full_backup.sql
```

### 2. Target System Requirements
- [ ] Verify target system OS compatibility
- [ ] Check target system disk space (minimum 5GB)
- [ ] Verify RAM available (minimum 4GB, recommended 8GB+)
- [ ] Confirm network connectivity and bandwidth
- [ ] Check firewall rules and port availability
- [ ] Verify system administrator access
- [ ] Document target system specifications

**System Requirements by Deployment Type:**

| Component | Docker | Native | Cloud (AWS) |
|-----------|--------|--------|------------|
| OS | Linux/Windows/macOS | Linux/Windows/macOS | Any |
| CPU | 2+ cores | 2+ cores | Variable |
| RAM | 4GB+ | 4GB+ | Variable |
| Disk | 5GB+ | 10GB+ | Auto-scaling |
| Network | 50Mbps+ | 50Mbps+ | High-speed |
| Python | N/A | 3.14+ | N/A |
| Docker | 20.10+ | N/A | N/A |

---

## Migration Steps

### Phase 1: Preparation (1-2 hours)

#### Step 1.1: Create Backup
- [ ] Backup source database
- [ ] Backup all configuration files
- [ ] Export current data
- [ ] Create application snapshot

**Commands:**
```bash
# Backup database
docker-compose exec mysql mysqldump -u fraud_user -p fraud_detection > fraud_detection_backup.sql

# Backup all data volumes
docker run --rm -v fraud_detection_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql_data_backup.tar.gz /data

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
docker cp fraud_detection_redis:/data/dump.rdb ./redis_backup.rdb

# Export environment
env | grep -E "MYSQL|DATABASE|SECRET|API" > environment_backup.env
```

#### Step 1.2: Document Current State
- [ ] Take screenshot of running system
- [ ] Document all endpoints and their responses
- [ ] Record user access patterns
- [ ] Note performance metrics

**Documentation Template:**
```markdown
# Current System State - $(date)

## Running Services
- API: http://current-system:8000 (Status: UP/DOWN)
- Dashboard: http://current-system:8501 (Status: UP/DOWN)
- Database: current-system:3307 (Status: UP/DOWN)
- Redis: current-system:6379 (Status: UP/DOWN)

## Database Info
- Size: {SIZE}MB
- Tables: {COUNT}
- Users: {COUNT}
- Last backup: {DATE/TIME}

## Performance Metrics
- API Response Time: {AVG}ms
- Database Query Time: {AVG}ms
- Memory Usage: {PERCENT}%
- CPU Usage: {PERCENT}%

## Custom Configurations
- {LIST CUSTOMIZATIONS}

## Known Issues
- {LIST ISSUES}
```

#### Step 1.3: Prepare Migration Plan
- [ ] Create detailed timeline
- [ ] Identify rollback plan
- [ ] Define success criteria
- [ ] Schedule maintenance window

---

### Phase 2: Environment Setup (30-60 minutes)

#### Step 2.1: Install Prerequisites on Target System

**Windows:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force; `
  [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol `
  -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install prerequisites
choco install docker-desktop git python -y

# Restart PowerShell or CMD
```

**Linux (Ubuntu/Debian):**
```bash
#!/bin/bash
set -e

echo "Installing prerequisites..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt-get install -y git

# Verify installations
docker --version
docker-compose --version
git --version

echo "Prerequisites installed successfully!"
```

**macOS:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install docker docker-compose git

# For Docker, download Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Homebrew: brew install docker

# Verify installations
docker --version
docker-compose --version
git --version
```

#### Step 2.2: Configure Network and Firewall
- [ ] Open required ports on firewall
  - 8000 (API)
  - 8501 (Dashboard)
  - 3307 (MySQL)
  - 6379 (Redis)
- [ ] Configure DNS if needed
- [ ] Set up VPN/SSH access
- [ ] Test network connectivity

**Firewall Rules:**
```bash
# Linux (UFW)
sudo ufw allow 8000/tcp
sudo ufw allow 8501/tcp
sudo ufw allow 3307/tcp
sudo ufw allow 6379/tcp

# Windows Firewall
netsh advfirewall firewall add rule name="FraudDetection-API" dir=in action=allow protocol=tcp localport=8000
netsh advfirewall firewall add rule name="FraudDetection-Dashboard" dir=in action=allow protocol=tcp localport=8501
```

#### Step 2.3: Prepare Storage
- [ ] Create backup directory
- [ ] Allocate space for database
- [ ] Set up log directory
- [ ] Configure data volumes

```bash
# Create directories
mkdir -p ~/fraud-detection/{data,logs,backups}
chmod 755 ~/fraud-detection/{data,logs,backups}

# For Docker volumes
docker volume create fraud_detection_mysql_data
docker volume create fraud_detection_redis_data
```

---

### Phase 3: Application Deployment (1-2 hours)

#### Step 3.1: Clone Repository
- [ ] Clone from repository
- [ ] Verify branch/tag
- [ ] Check integrity

```bash
# Clone repository
git clone <repository-url> fraud-detection
cd fraud-detection

# Verify correct branch
git branch -a
git checkout main  # or desired branch

# Verify tag/version
git tag -l
```

#### Step 3.2: Configure Application

**Copy environment template:**
```bash
cp .env.example .env
```

**Edit .env with appropriate values:**
```env
# Database Configuration
MYSQL_ROOT_PASSWORD=<GENERATE_STRONG_PASSWORD>
MYSQL_DATABASE=fraud_detection
MYSQL_USER=fraud_user
MYSQL_PASSWORD=<GENERATE_STRONG_PASSWORD>

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=mysql+pymysql://fraud_user:<PASSWORD>@mysql:3306/fraud_detection

# Security
SECRET_KEY=<GENERATE_WITH: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_EXPIRATION_HOURS=24

# Environment
ENVIRONMENT=production
DEBUG=False

# Redis
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/api.log
```

**Generate secure password:**
```bash
# Linux/macOS
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Windows PowerShell
[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes(([guid]::NewGuid()).ToString())) | ForEach-Object { $_.Substring(0, 32) }
```

#### Step 3.3: Build and Start Services

```bash
# Build Docker images
docker-compose build --no-cache

# Start services in background
docker-compose up -d

# Monitor startup
docker-compose logs -f

# Check service status
docker-compose ps
```

#### Step 3.4: Verify Services Are Running

```bash
# Check all services
docker-compose ps

# Expected output:
# NAME                      COMMAND                STATUS          PORTS
# fraud_detection_mysql      "docker-entrypoint..."   Up (healthy)    0.0.0.0:3307->3306/tcp
# fraud_detection_redis      "redis-server"          Up (healthy)    0.0.0.0:6379->6379/tcp
# fraud_detection_api        "python run.py"         Up              0.0.0.0:8000->8000/tcp
# fraud_detection_dashboard  "streamlit run..."      Up              0.0.0.0:8501->8501/tcp
```

---

### Phase 4: Data Migration (1-3 hours)

#### Step 4.1: Restore Database

**Option A: Restore from backup**
```bash
# If you have a backup SQL file
docker-compose exec -T mysql mysql -u fraud_user -p fraud_detection < fraud_detection_backup.sql

# Verify restoration
docker-compose exec mysql mysql -u fraud_user -p -e "USE fraud_detection; SHOW TABLES; SELECT COUNT(*) FROM users;"
```

**Option B: Run migrations and seed data**
```bash
# Run database migrations
docker-compose exec api python run_migrations.py

# Seed with sample data
docker-compose exec api python seed_database.py

# Verify data
docker-compose exec mysql mysql -u fraud_user -p -e "USE fraud_detection; SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM transactions;"
```

#### Step 4.2: Verify Data Integrity

```bash
# Check data consistency
docker-compose exec api python -c "
from app.database import SessionLocal
from app.models import User, Transaction

db = SessionLocal()
users = db.query(User).count()
transactions = db.query(Transaction).count()
print(f'Users: {users}')
print(f'Transactions: {transactions}')
"

# Compare with source system
# SOURCE_USERS=1234
# SOURCE_TRANSACTIONS=56789
# echo "Source: Users=$SOURCE_USERS, Transactions=$SOURCE_TRANSACTIONS"
# echo "Target: Users=$users, Transactions=$transactions"
```

#### Step 4.3: Database Optimization

```bash
# Create indexes for performance
docker-compose exec mysql mysql -u fraud_user -p fraud_detection << EOF
CREATE INDEX idx_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_user_id ON transactions(user_id);
CREATE INDEX idx_fraud_flag ON transactions(fraud_flag);
CREATE INDEX idx_amount ON transactions(amount);

-- Optimize tables
OPTIMIZE TABLE transactions;
OPTIMIZE TABLE users;
OPTIMIZE TABLE models;
EOF

# Check optimization
docker-compose exec mysql mysql -u fraud_user -p -e "SHOW INDEX FROM fraud_detection.transactions;"
```

---

### Phase 5: Application Testing (1-2 hours)

#### Step 5.1: Health Checks

```bash
# Wait for services to stabilize
sleep 30

# API Health
curl -X GET http://localhost:8000/health
# Expected: {"status": "healthy"}

# Database Health
curl -X GET http://localhost:8000/api/v1/health/db
# Expected: {"status": "healthy"}

# Full System Health
curl -X GET http://localhost:8000/api/v1/health/system
# Expected: complete system status
```

#### Step 5.2: Functional Tests

```bash
# Run test suite
docker-compose exec api pytest tests/ -v

# Run specific test
docker-compose exec api pytest tests/test_api.py -v

# Run with coverage
docker-compose exec api pytest tests/ --cov=app --cov-report=html
```

#### Step 5.3: Manual Testing

```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/v1/users
curl -X GET http://localhost:8000/api/v1/transactions?limit=10
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "merchant_category": "grocery"}'

# Access Dashboard
# Open browser: http://localhost:8501

# Check API Documentation
# Open browser: http://localhost:8000/docs
```

#### Step 5.4: Performance Testing

```bash
# Load test API
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Using wrk
# wrk -t4 -c100 -d30s http://localhost:8000/api/v1/health

# Monitor performance
docker-compose stats
```

---

### Phase 6: Post-Deployment (30-60 minutes)

#### Step 6.1: Backup Verification
- [ ] Verify backup was created
- [ ] Test backup restoration
- [ ] Document backup procedure

```bash
# Create initial backup
docker-compose exec mysql mysqldump -u fraud_user -p fraud_detection > post_deployment_backup.sql
ls -lah post_deployment_backup.sql

# Test restore (on backup)
mysql -u fraud_user -p fraud_detection < post_deployment_backup.sql
```

#### Step 6.2: Monitoring and Logging Setup

```bash
# Check logs
docker-compose logs --tail=50

# View specific service logs
docker-compose logs -f api
docker-compose logs -f mysql
docker-compose logs -f dashboard

# Export logs
docker-compose logs > full_system_logs.txt
```

#### Step 6.3: Security Hardening
- [ ] Change default passwords
- [ ] Configure SSL/TLS
- [ ] Enable authentication
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Enable logging and monitoring

```bash
# Generate SSL certificate (self-signed for dev)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update docker-compose.yml to use SSL
# Update API_URL to use https://
```

#### Step 6.4: Documentation Update
- [ ] Update deployment guide
- [ ] Document any modifications
- [ ] Create runbook for operations
- [ ] Document access procedures
- [ ] Create troubleshooting guide

---

### Phase 7: Cutover (Scheduled Downtime)

#### Step 7.1: Pre-Cutover
- [ ] Notify all users of maintenance window
- [ ] Stop application on source system
- [ ] Final backup of source database
- [ ] Verify all data is synced

```bash
# On source system
docker-compose down
docker-compose exec mysql mysqldump -u fraud_user -p fraud_detection > final_backup.sql
# Transfer final_backup.sql to target system
```

#### Step 7.2: Cutover
- [ ] Import final backup on target system
- [ ] Verify data integrity
- [ ] Update DNS/load balancer
- [ ] Update application URLs
- [ ] Verify connectivity

```bash
# On target system
docker-compose exec -T mysql mysql -u fraud_user -p fraud_detection < final_backup.sql

# Verify data
docker-compose exec mysql mysql -u fraud_user -p -e "SELECT COUNT(*) FROM fraud_detection.transactions;"

# Restart services
docker-compose restart api dashboard
```

#### Step 7.3: Post-Cutover Verification
- [ ] Test all major functionality
- [ ] Verify user access
- [ ] Check data accuracy
- [ ] Monitor for errors

---

## Rollback Plan

### If Critical Issues Occur

```bash
# Step 1: Stop new system
docker-compose down

# Step 2: Restore source system
# cd /path/to/source/system
# docker-compose up -d

# Step 3: Restore from backup if needed
docker-compose exec mysql mysql -u fraud_user -p fraud_detection < rollback_backup.sql

# Step 4: Verify source is operational
curl http://source-system:8000/health

# Step 5: Notify stakeholders
# - Indicate rollback was performed
# - Begin investigation
# - Plan proper migration
```

### Rollback Criteria
- [ ] More than 5% of requests failing
- [ ] Database corruption detected
- [ ] Security breach identified
- [ ] Data loss or inconsistency
- [ ] Critical functionality non-operational

---

## Post-Migration Support

### Monitoring Checklist
- [ ] Set up application monitoring (e.g., Prometheus, Grafana)
- [ ] Configure log aggregation
- [ ] Set up alerts for critical events
- [ ] Enable health check monitoring
- [ ] Monitor database performance

### Maintenance Tasks
- [ ] Schedule regular backups
- [ ] Plan database maintenance windows
- [ ] Update dependencies monthly
- [ ] Review security logs weekly
- [ ] Optimize database queries

### Documentation
- [ ] Maintain runbooks
- [ ] Keep disaster recovery plan
- [ ] Document custom configurations
- [ ] Update architecture diagrams
- [ ] Create troubleshooting guides

---

## Success Criteria

✓ Migration is successful when:
- [ ] All services are running and healthy
- [ ] API responds to all requests correctly
- [ ] Dashboard displays accurate data
- [ ] Database integrity is verified
- [ ] All tests pass
- [ ] Performance meets baseline
- [ ] No errors in logs
- [ ] Users can access the system
- [ ] Data is identical to source system
- [ ] Backups can be restored successfully

---

## Contact & Support

**If issues occur:**
1. Check `DEPLOYMENT_GUIDE.md` for troubleshooting
2. Review `OPERATIONS_RUNBOOK.md` for operational procedures
3. Check application logs: `docker-compose logs -f`
4. Consult documentation in `/docs`

**Useful Commands:**
```bash
docker-compose ps                   # Service status
docker-compose logs -f              # Live logs
docker-compose logs -f api          # API logs only
docker-compose restart              # Restart services
docker-compose down                 # Stop services
docker-compose exec api bash        # Shell access
```

---

**Document Version**: 1.0  
**Last Updated**: October 2024  
**Status**: ✅ Ready for Use
