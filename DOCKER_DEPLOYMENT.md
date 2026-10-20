# Docker Deployment Guide for Fraud Detection Dashboard

## Overview

This guide provides complete instructions for deploying the Fraud Detection Dashboard using Docker and Docker Compose. It covers development, staging, and production deployments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
4. [Environment Configuration](#environment-configuration)
5. [Running Services](#running-services)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Database Management](#database-management)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: For cloning the repository
- **curl**: For health checks and testing

### System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Production**: 16GB+ RAM, 8+ CPU cores, 100GB+ storage

### Port Availability

Ensure these ports are available:
- **8000**: FastAPI backend
- **8501**: Streamlit dashboard
- **5432**: PostgreSQL database
- **6379**: Redis cache
- **5050**: pgAdmin (optional)
- **80/443**: Nginx reverse proxy (production)

---

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd Financial\ Risk\ Analysis\ and\ Hybrid\ Fraud\ Detection\ System
```

### 2. Create Environment Files

Copy and customize the template:

```bash
# Copy dashboard configuration
cp .env.dashboard.template .env.dashboard

# Copy backend configuration (if exists)
cp backend/.env.example backend/.env 2>/dev/null || true
```

### 3. Edit Configuration Files

Edit `.env.dashboard`:

```env
# Dashboard Settings
API_BASE_URL=http://api:8000
SESSION_TIMEOUT_MINUTES=15
DEBUG_MODE=true
STREAMLIT_LOG_LEVEL=info

# API Settings
JWT_SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@db:5432/fraud_db
```

### 4. Build Images

```bash
# Build both services
docker-compose -f docker-compose.dashboard.yml build

# Or build specific service
docker-compose -f docker-compose.dashboard.yml build dashboard
docker-compose -f docker-compose.dashboard.yml build api
```

### 5. Start Development Environment

```bash
# Start all services with logs
docker-compose -f docker-compose.dashboard.yml up

# Or start in background
docker-compose -f docker-compose.dashboard.yml up -d

# View logs
docker-compose -f docker-compose.dashboard.yml logs -f dashboard
docker-compose -f docker-compose.dashboard.yml logs -f api
docker-compose -f docker-compose.dashboard.yml logs -f db
```

### 6. Verify Services

```bash
# Check status
docker-compose -f docker-compose.dashboard.yml ps

# Test API
curl http://localhost:8000/health

# Test Dashboard (should return HTML)
curl http://localhost:8501 | head -20
```

---

## Production Setup

### 1. Pre-deployment Checklist

- [ ] All environment variables configured
- [ ] SSL certificates obtained (Let's Encrypt recommended)
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Disaster recovery plan documented

### 2. Create Production Environment File

```bash
cp .env.dashboard.template .env.dashboard.prod
```

Edit `.env.dashboard.prod` with production values:

```env
# Production Settings
API_BASE_URL=https://fraud-detection.example.com/api
SESSION_TIMEOUT_MINUTES=15
DEBUG_MODE=false
STREAMLIT_LOG_LEVEL=warning

# Security
JWT_SECRET_KEY=<strong-random-key-min-32-chars>
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_SSL_KEYFILE=/run/secrets/ssl_key
STREAMLIT_SERVER_SSL_CERTFILE=/run/secrets/ssl_cert

# Database (use strong password)
POSTGRES_PASSWORD=<strong-password>
```

### 3. Configure SSL Certificates

#### Option A: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d fraud-detection.example.com

# Copy to project directory
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/fraud-detection.example.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/fraud-detection.example.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*
```

#### Option B: Self-signed Certificate (testing only)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem -keyout ssl/key.pem -days 365 \
  -subj "/CN=fraud-detection.example.com"
```

### 4. Configure Nginx

Edit `nginx.conf`:

```nginx
# Update server_name
server_name fraud-detection.example.com;

# Update certificate paths
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;

# Update upstream addresses if different
upstream api_backend {
    server api:8000;
}
```

### 5. Configure Database Backups

Create `backup-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/fraud-detection"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fraud_db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

docker-compose -f docker-compose.dashboard.yml exec -T db \
  pg_dump -U postgres fraud_db | gzip > "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

Set up daily backups with cron:

```bash
chmod +x backup-db.sh

# Add to crontab
crontab -e

# Add line:
0 2 * * * /path/to/backup-db.sh
```

### 6. Deploy with Production Profile

```bash
# Build images with optimizations
docker-compose -f docker-compose.dashboard.yml \
  --env-file .env.dashboard.prod \
  --profile production \
  build

# Start services
docker-compose -f docker-compose.dashboard.yml \
  --env-file .env.dashboard.prod \
  --profile production \
  up -d

# Verify all services
docker-compose -f docker-compose.dashboard.yml ps
```

---

## Environment Configuration

### Dashboard Variables

```env
# API Configuration
API_BASE_URL=http://api:8000              # Backend URL
API_TIMEOUT_SECONDS=30                    # Request timeout

# Session Management
SESSION_TIMEOUT_MINUTES=15                # Inactivity timeout
MAX_LOGIN_ATTEMPTS=5                      # Failed login attempts
LOGIN_LOCKOUT_MINUTES=15                  # Lockout duration

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true            # No browser auto-open
STREAMLIT_SERVER_PORT=8501                # Listen port
STREAMLIT_SERVER_ADDRESS=0.0.0.0          # Listen address
STREAMLIT_LOGGER_LEVEL=info               # Log level

# Debug and Logging
DEBUG_MODE=false                          # Enable debug output
LOG_LEVEL=info                            # Application log level
LOG_FORMAT=json                           # Log format (json/text)
```

### Backend Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@db:5432/fraud_db
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600

# Security
JWT_SECRET_KEY=<strong-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Cache
REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=3600

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## Running Services

### Start All Services

```bash
# Development
docker-compose -f docker-compose.dashboard.yml up

# Production (with Nginx)
docker-compose -f docker-compose.dashboard.yml \
  --profile production up -d
```

### Stop Services

```bash
# Stop and remove containers
docker-compose -f docker-compose.dashboard.yml down

# Also remove volumes (careful - deletes data!)
docker-compose -f docker-compose.dashboard.yml down -v
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.dashboard.yml logs -f

# Specific service
docker-compose -f docker-compose.dashboard.yml logs -f dashboard
docker-compose -f docker-compose.dashboard.yml logs -f api
docker-compose -f docker-compose.dashboard.yml logs -f db

# Last 100 lines
docker-compose -f docker-compose.dashboard.yml logs --tail=100 dashboard
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.dashboard.yml restart

# Restart specific
docker-compose -f docker-compose.dashboard.yml restart dashboard

# Rebuild and restart
docker-compose -f docker-compose.dashboard.yml up -d --build dashboard
```

### Execute Commands in Container

```bash
# Run command in api container
docker-compose -f docker-compose.dashboard.yml exec api python -m pytest

# Run psql in database
docker-compose -f docker-compose.dashboard.yml exec db psql -U postgres -d fraud_db

# Run shell in dashboard
docker-compose -f docker-compose.dashboard.yml exec dashboard /bin/bash
```

---

## Health Checks & Monitoring

### Manual Health Checks

```bash
# API health
curl -s http://localhost:8000/health | jq .

# Dashboard health
curl -s http://localhost:8501/_stcore/health

# Database health
docker-compose -f docker-compose.dashboard.yml exec db pg_isready -U postgres

# Redis health
docker-compose -f docker-compose.dashboard.yml exec redis redis-cli ping
```

### Container Status

```bash
# View container status
docker-compose -f docker-compose.dashboard.yml ps

# View resource usage
docker stats

# View logs for failed containers
docker-compose -f docker-compose.dashboard.yml logs --tail=50 <service_name>
```

### Application Monitoring

```bash
# Check API metrics endpoint (if implemented)
curl http://localhost:8000/metrics

# Check dashboard memory usage
docker stats fraud-dashboard

# View container resource limits
docker inspect fraud-dashboard | jq '.HostConfig.Memory'
```

---

## Database Management

### Database Operations

```bash
# Connect to database
docker-compose -f docker-compose.dashboard.yml exec db psql -U postgres -d fraud_db

# Run SQL file
docker-compose -f docker-compose.dashboard.yml exec -T db psql -U postgres -d fraud_db < script.sql

# Backup database
docker-compose -f docker-compose.dashboard.yml exec -T db \
  pg_dump -U postgres fraud_db > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.dashboard.yml exec -T db \
  psql -U postgres -d fraud_db

# Reset database
docker-compose -f docker-compose.dashboard.yml down -v
docker-compose -f docker-compose.dashboard.yml up -d db
```

### pgAdmin Access

```
URL: http://localhost:5050
Email: admin@example.com
Password: admin
```

Steps to connect in pgAdmin:
1. Register server: right-click "Servers" > "Register" > "Server"
2. General tab: Name = "Fraud DB"
3. Connection tab:
   - Host: db
   - Port: 5432
   - Username: postgres
   - Password: postgres
   - Database: fraud_db
4. Click "Save"

---

## SSL/TLS Configuration

### Generate Self-signed Certificate (Development)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ssl/key.pem -out ssl/cert.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"
```

### Let's Encrypt Setup (Production)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone \
  -d fraud-detection.example.com \
  -d www.fraud-detection.example.com

# Copy to project
sudo cp /etc/letsencrypt/live/fraud-detection.example.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/fraud-detection.example.com/privkey.pem ssl/key.pem

# Setup auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Test SSL Configuration

```bash
# Test SSL certificate
openssl s_client -connect fraud-detection.example.com:443

# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Verify SSL with curl
curl -v --cacert ssl/cert.pem https://fraud-detection.example.com
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
docker ps

# Check disk space
df -h

# Check port conflicts
sudo lsof -i :8000 -i :8501 -i :5432

# Check logs
docker-compose -f docker-compose.dashboard.yml logs
```

#### Database Connection Errors

```bash
# Verify database is running
docker-compose -f docker-compose.dashboard.yml ps db

# Check database logs
docker-compose -f docker-compose.dashboard.yml logs db

# Test connection
docker-compose -f docker-compose.dashboard.yml exec db \
  pg_isready -h localhost -U postgres
```

#### API Not Responding

```bash
# Check API container
docker-compose -f docker-compose.dashboard.yml ps api

# View API logs
docker-compose -f docker-compose.dashboard.yml logs api

# Test API health
curl -v http://localhost:8000/health

# Restart API
docker-compose -f docker-compose.dashboard.yml restart api
```

#### Dashboard Not Loading

```bash
# Check dashboard container
docker-compose -f docker-compose.dashboard.yml ps dashboard

# View dashboard logs
docker-compose -f docker-compose.dashboard.yml logs dashboard

# Clear streamlit cache
docker-compose -f docker-compose.dashboard.yml exec dashboard \
  rm -rf ~/.streamlit/cache
```

#### Network Issues

```bash
# Check network
docker network ls
docker network inspect fraud_network

# Restart network
docker-compose -f docker-compose.dashboard.yml down
docker-compose -f docker-compose.dashboard.yml up -d

# Test DNS resolution
docker-compose -f docker-compose.dashboard.yml exec dashboard ping api
```

### Debug Mode

Enable debug logging:

```bash
# Edit .env file
DEBUG_MODE=true
STREAMLIT_LOGGER_LEVEL=debug

# Restart services
docker-compose -f docker-compose.dashboard.yml restart
```

### View Container Internals

```bash
# Enter container shell
docker-compose -f docker-compose.dashboard.yml exec dashboard /bin/bash

# Install debugging tools
apt-get update && apt-get install -y curl wget vim

# Check environment
env | grep -E "API|DB|REDIS"
```

---

## Security Best Practices

### Container Security

```bash
# Use read-only filesystem where possible
# Run containers as non-root (already done in Dockerfile)
# Keep images minimal (use slim/alpine where possible)
# Don't run privileged containers
# Limit resource usage
```

### Network Security

```bash
# Use internal Docker network for inter-service communication
# Expose only necessary ports to host
# Use HTTPS for external traffic
# Implement rate limiting (already in nginx.conf)
# Use security headers (already in nginx.conf)
```

### Secret Management

```bash
# Never commit secrets to git
# Use environment files (.env) - add to .gitignore
# Use Docker secrets for production (Docker Swarm)
# Rotate secrets regularly
# Use strong, random values for all secrets

# Generate random secret
openssl rand -base64 32
```

### Database Security

```bash
# Change default database password
# Restrict database access (firewall rules)
# Enable database backups
# Use SSL connections to database
# Regular security updates

# Update password in .env
POSTGRES_PASSWORD=<strong-password>
```

### Image Security

```bash
# Regularly rebuild images with latest dependencies
docker-compose -f docker-compose.dashboard.yml build --no-cache

# Scan images for vulnerabilities
docker scan fraud-dashboard:latest
docker scan fraud-api:latest

# Use trusted base images
# Pin image versions (no 'latest' tag)
```

### Monitoring & Logging

```bash
# Enable logging for all containers
docker-compose -f docker-compose.dashboard.yml logs -f

# Monitor resource usage
docker stats

# Set up external logging
# Configure centralized log aggregation
# Monitor security events
```

---

## Performance Optimization

### Resource Limits

Update `docker-compose.dashboard.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
  
  db:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Caching Strategy

```bash
# Redis is already configured
# Configure cache TTL in .env
CACHE_TTL_SECONDS=3600

# Monitor cache hits
docker-compose -f docker-compose.dashboard.yml exec redis \
  redis-cli info stats
```

### Database Optimization

```bash
# Check database logs for slow queries
docker-compose -f docker-compose.dashboard.yml exec db \
  psql -U postgres -d fraud_db -c "SELECT * FROM pg_stat_statements"

# Create indexes if needed
docker-compose -f docker-compose.dashboard.yml exec -T db psql -U postgres -d fraud_db <<EOF
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
EOF
```

---

## Maintenance Schedule

### Daily
- Monitor service health
- Check logs for errors
- Monitor resource usage

### Weekly
- Review security logs
- Backup database
- Update dependencies (development)

### Monthly
- Security patches
- Performance analysis
- Disaster recovery drill

### Quarterly
- Security audit
- Capacity planning
- Architecture review

---

## Support and Escalation

### Error Codes Reference

| Code | Issue | Solution |
|------|-------|----------|
| 137 | Out of memory | Increase memory limit, check for leaks |
| 139 | Segmentation fault | Restart container, update dependencies |
| 1 | General error | Check logs, verify configuration |
| 2 | Misuse of commands | Check docker-compose syntax |

### Getting Help

1. Check logs: `docker-compose logs -f <service>`
2. Review Docker documentation: https://docs.docker.com
3. Check service health: Health check endpoints
4. Verify configuration: Review .env files
5. Test connectivity: Use curl to test endpoints

---

## Appendix: Quick Commands

```bash
# Start all services
docker-compose -f docker-compose.dashboard.yml up -d

# Stop all services
docker-compose -f docker-compose.dashboard.yml down

# View logs
docker-compose -f docker-compose.dashboard.yml logs -f

# Check status
docker-compose -f docker-compose.dashboard.yml ps

# Rebuild images
docker-compose -f docker-compose.dashboard.yml build --no-cache

# Execute command in container
docker-compose -f docker-compose.dashboard.yml exec <service> <command>

# Database backup
docker-compose -f docker-compose.dashboard.yml exec -T db \
  pg_dump -U postgres fraud_db | gzip > backup.sql.gz

# Clean everything (careful!)
docker-compose -f docker-compose.dashboard.yml down -v && \
  docker system prune -a -f
```

---

## Document Version

- **Version**: 1.0
- **Last Updated**: 2024
- **Maintained By**: DevOps Team
- **Next Review**: [Quarterly]
