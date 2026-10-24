# Operations Runbook

## Financial Risk Analysis & Hybrid Fraud Detection System

Procedures and guidelines for operating the Fraud Detection System in production.

## Table of Contents

1. [Startup Procedures](#startup-procedures)
2. [Shutdown Procedures](#shutdown-procedures)
3. [Health Monitoring](#health-monitoring)
4. [Common Issues and Resolutions](#common-issues-and-resolutions)
5. [Backup and Recovery](#backup-and-recovery)
6. [Performance Tuning](#performance-tuning)
7. [Scaling Guidelines](#scaling-guidelines)

## Startup Procedures

### Before Startup Checklist

- [ ] Database connection verified
- [ ] All services have disk space (>1GB)
- [ ] Memory available (>2GB free)
- [ ] No port conflicts (8000, 8501, 3306, 6379)
- [ ] Network connectivity verified
- [ ] SSL/TLS certificates current
- [ ] Environment variables loaded

### Docker Startup (Recommended)

```bash
# 1. Navigate to project directory
cd /path/to/project

# 2. Verify docker-compose.yml is configured correctly
cat docker-compose.yml

# 3. Start all services
docker-compose up -d

# 4. Wait 30 seconds for services to initialize
sleep 30

# 5. Verify all containers started
docker-compose ps

# Expected output:
# NAME         STATUS
# mysql        healthy
# redis        healthy
# api          running
# dashboard    running

# 6. Check logs for errors
docker-compose logs

# 7. Verify health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

### Kubernetes Startup (Enterprise)

```bash
# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods
kubectl get svc

# Check status
kubectl describe pod fraud-detection-api-xxx
```

### Local Development Startup

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Set environment variables
export DATABASE_URL="mysql://user:pass@localhost:3306/fraud_detection"
export DEBUG="true"

# 3. Start API server (Terminal 1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start Dashboard (Terminal 2)
streamlit run dashboard/app.py

# 5. Monitor startup
# Watch for "Uvicorn running on http://0.0.0.0:8000"
# Watch for "You can now view your Streamlit app in your browser"
```

## Shutdown Procedures

### Graceful Shutdown (Docker)

```bash
# 1. Stop all services (gives 10 seconds to gracefully shutdown)
docker-compose down

# 2. Verify containers stopped
docker-compose ps

# 3. Check if any lingering processes
docker ps -a | grep fraud-detection
```

### Emergency Shutdown

```bash
# Force stop all containers
docker-compose kill

# Remove containers
docker-compose rm -f

# Check and remove dangling resources
docker network prune -f
docker volume prune -f
```

### Backup Before Shutdown

```bash
# Create backup
python scripts/backup_database.py

# Verify backup
ls -lh backup/

# Optionally upload to external storage
aws s3 cp backup/fraud_detection_backup_*.sql.gz s3://backups/
```

## Health Monitoring

### Health Check Endpoints

```bash
# Basic health
curl http://localhost:8000/health
# Expected: { "status": "healthy" }

# Ready check (dependencies)
curl http://localhost:8000/health/ready
# Expected: { "status": "ready", "database": "connected" }

# Liveness check
curl http://localhost:8000/health/live
# Expected: 200 OK

# Dashboard health (Streamlit)
curl http://localhost:8501/_stcore/health
# Expected: 200 OK
```

### Monitoring Dashboard

Access monitoring at:
- **Streamlit Dashboard**: http://localhost:8501
- **Grafana (if configured)**: http://localhost:3000
- **Prometheus (if configured)**: http://localhost:9090

### Key Metrics to Monitor

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| API Response Time | <200ms | >300ms | >500ms |
| Database Query Time | <100ms | >200ms | >500ms |
| Error Rate | <0.1% | >1% | >5% |
| Memory Usage | <50% | >70% | >85% |
| Disk Usage | <70% | >80% | >90% |
| Database Connections | <10 | >15 | >20 |
| Request Rate | <100/sec | >200/sec | >500/sec |

### Monitoring Commands

```bash
# Docker container stats
docker stats --no-stream

# Database connections
mysql -u user -p -e "SHOW PROCESSLIST;"

# API logs
docker-compose logs api --tail 100

# Check disk space
df -h

# Check memory usage
free -h

# System load
uptime
```

## Common Issues and Resolutions

### Issue: API Container Won't Start

**Symptoms**: Container exits immediately, health check fails

**Debug Steps**:
```bash
# Check logs
docker-compose logs api

# Common error causes:
# - "Connection refused": Database not running
# - "Permission denied": Docker permissions issue
# - "Port already in use": Change port in docker-compose.yml
```

**Resolution**:
```bash
# Option 1: Database issue
docker-compose up mysql
sleep 10
docker-compose up api

# Option 2: Port conflict
docker ps | grep 8000
kill -9 <PID>
docker-compose up api

# Option 3: Permission issue
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Database Connection Timeout

**Symptoms**: "Connection timeout", "Max retries exceeded"

**Debug Steps**:
```bash
# Check database is running
docker-compose ps mysql

# Check database logs
docker-compose logs mysql

# Verify connectivity
mysql -h localhost -u fraud_user -p -e "SELECT 1"
```

**Resolution**:
```bash
# Restart database
docker-compose restart mysql
sleep 10

# Check connection pool settings
echo "SHOW VARIABLES LIKE 'max_connections';" | mysql -u root -p

# Increase if needed
docker-compose exec mysql mysql -u root -p \
  -e "SET GLOBAL max_connections = 100;"
```

### Issue: High Memory Usage

**Symptoms**: Container killed by OOM, system slow

**Debug Steps**:
```bash
# Check memory usage
docker stats api

# Check for memory leaks
ps aux | grep python

# Check MySQL memory
mysql -u root -p -e "SHOW STATUS LIKE '%memory%';"
```

**Resolution**:
```bash
# Restart service
docker-compose restart api

# Optimize queries (if database issue)
mysql -u root -p < optimization.sql

# Increase container memory in docker-compose.yml
# mem_limit: 2g
docker-compose up -d
```

### Issue: Slow Transaction Processing

**Symptoms**: <50ms target not met, API timeouts

**Debug Steps**:
```bash
# Check query performance
mysql -u root -p \
  -e "SELECT * FROM mysql.slow_log LIMIT 10;"

# Monitor active queries
mysql -u root -p -e "SHOW PROCESSLIST;"

# Check database indexes
mysql -u root -p fraud_detection \
  -e "SHOW INDEX FROM transactions;"
```

**Resolution**:
```bash
# Enable slow query log
docker-compose exec mysql mysql -u root -p \
  -e "SET GLOBAL slow_query_log = 'ON'; SET GLOBAL long_query_time = 0.5;"

# Add missing indexes
python run_migrations.py upgrade

# Analyze query execution
EXPLAIN SELECT ...;
```

### Issue: Dashboard Not Responsive

**Symptoms**: 503 errors, slow dashboard loading

**Debug Steps**:
```bash
# Check dashboard logs
docker-compose logs dashboard --tail 50

# Verify Streamlit is running
docker-compose ps dashboard

# Test connectivity
curl -I http://localhost:8501
```

**Resolution**:
```bash
# Restart dashboard
docker-compose restart dashboard

# Clear Streamlit cache
docker-compose exec dashboard rm -rf ~/.streamlit/

# Increase Streamlit resources in docker-compose.yml
docker-compose up -d
```

## Backup and Recovery

### Automated Backup

```bash
# Create daily backup (add to crontab)
0 2 * * * cd /path/to/project && python scripts/backup_database.py

# Verify backup cron
crontab -l | grep backup_database
```

### Manual Backup

```bash
# Full database backup
python scripts/backup_database.py

# Backup with specific retention
python scripts/backup_database.py --retention-days 60

# Backup specific table
mysqldump -u user -p fraud_detection transactions > transactions_backup.sql

# List backups
ls -lh backup/
```

### Backup Verification

```bash
# Verify backup integrity
tar -tzf backup/fraud_detection_backup_*.sql.gz > /dev/null && echo "OK"

# Check backup size
du -sh backup/fraud_detection_backup_*.sql.gz

# Verify backup can be restored (TEST ONLY)
# mysql -u root -p fraud_detection < test_backup.sql
```

### Recovery Procedure

**Preparation**:
1. Stop all services: `docker-compose down`
2. Create backup of current database (if possible)
3. Prepare restoration database

**Step 1: Restore Database**

```bash
# Option A: Restore from gzipped backup
gunzip < backup/fraud_detection_backup_2024-01-01_02-00-00.sql.gz | \
  mysql -u root -p fraud_detection

# Option B: Restore from uncompressed backup
mysql -u root -p fraud_detection < backup/fraud_detection_backup.sql

# Verify restoration
mysql -u root -p fraud_detection -e "SELECT COUNT(*) FROM transactions;"
```

**Step 2: Verify Data Integrity**

```bash
# Check row counts
mysql -u root -p fraud_detection -e "
SELECT 'transactions' as table_name, COUNT(*) FROM transactions UNION
SELECT 'alerts', COUNT(*) FROM alerts UNION
SELECT 'cases', COUNT(*) FROM cases;
"

# Check for orphaned records
SELECT * FROM alerts WHERE transaction_id NOT IN (SELECT id FROM transactions);
```

**Step 3: Restart Services**

```bash
# Start services
docker-compose up -d

# Wait for services to initialize
sleep 30

# Verify health
curl http://localhost:8000/health/ready
```

**Step 4: Post-Recovery Validation**

```bash
# Run smoke tests
pytest tests/test_smoke.py -v

# Check application logs
docker-compose logs api

# Verify dashboard
# Open http://localhost:8501
```

## Performance Tuning

### Database Optimization

```bash
# Enable slow query log
mysql -u root -p -e "SET GLOBAL slow_query_log = 1;"

# Analyze tables
mysql -u root -p fraud_detection -e "
ANALYZE TABLE transactions;
ANALYZE TABLE alerts;
ANALYZE TABLE investigation_cases;
"

# Optimize tables
mysql -u root -p fraud_detection -e "
OPTIMIZE TABLE transactions;
OPTIMIZE TABLE alerts;
"

# Check query cache (if enabled)
mysql -u root -p -e "SHOW STATUS LIKE '%Qcache%';"
```

### Connection Pool Tuning

Update in `.env`:

```bash
# Connection pool settings
DB_POOL_SIZE=20          # max connections
DB_POOL_RECYCLE=3600     # recycle connections every hour
DB_POOL_TIMEOUT=30       # timeout in seconds
DB_POOL_PRE_PING=true    # test connections before use
```

### API Performance

```bash
# Optimize API response
# 1. Enable response compression
# 2. Implement caching headers
# 3. Use database query optimization
# 4. Implement pagination (default: 50 items)
```

### Memory Optimization

```bash
# Check memory usage by table
SELECT TABLE_NAME, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'fraud_detection'
ORDER BY size_mb DESC;

# Archive old audit logs (keep 90 days)
DELETE FROM audit_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

## Scaling Guidelines

### Vertical Scaling (Increase Resources)

For performance bottlenecks:

```bash
# Increase container memory in docker-compose.yml
services:
  api:
    mem_limit: 4g  # Increase from 2g
  mysql:
    mem_limit: 8g  # Increase from 4g
```

### Horizontal Scaling (Multiple Instances)

For load distribution:

```bash
# Docker Swarm or Kubernetes deployment
# Multiple API instances behind load balancer
# RDS or managed MySQL for database

# Example: 3 API instances
services:
  api:
    deploy:
      replicas: 3
```

### Database Scaling

When database reaches capacity:

1. **Read Replicas**: Add read-only MySQL replicas
2. **Sharding**: Partition data by customer ID
3. **Caching**: Add Redis caching layer
4. **Archiving**: Archive old data to cold storage

### Load Balancer Configuration

```bash
# Example: Nginx load balancer
upstream api_servers {
  server api-1:8000;
  server api-2:8000;
  server api-3:8000;
}

server {
  location / {
    proxy_pass http://api_servers;
  }
}
```

---

**Version**: 1.0.0
**Last Updated**: 2024-01-01
**Maintainer**: DevOps Team
