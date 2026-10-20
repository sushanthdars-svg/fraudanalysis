# Fraud Detection Dashboard - Deployment Infrastructure

Production-ready Docker configuration and CI/CD pipeline for the Fraud Detection Dashboard system.

## Files Overview

### Docker Configuration Files

#### 1. **Dockerfile.dashboard** (60 lines)
Optimized multi-stage Dockerfile for Streamlit dashboard:
- **Builder stage**: Creates minimal Python environment with dependencies
- **Runtime stage**: Slim base image with only runtime requirements
- **Non-root user**: Security hardening with unprivileged app user
- **Health checks**: Container health monitoring enabled
- **Environment config**: Streamlit-specific settings for production

#### 2. **Dockerfile.api** (40 lines)
Template Dockerfile for FastAPI backend:
- **Multi-stage build**: Optimizes image size
- **Python 3.11**: Latest stable version
- **Uvicorn workers**: 4 workers for production load
- **Health check**: API health monitoring
- **Non-root execution**: Security best practice

#### 3. **docker-compose.dashboard.yml** (180 lines)
Complete multi-container orchestration including:
- **fraud-api**: FastAPI backend service
- **fraud-dashboard**: Streamlit frontend
- **fraud-db**: PostgreSQL database
- **fraud-redis**: Redis cache
- **fraud-pgadmin**: Database management UI (optional)
- **fraud-nginx**: Reverse proxy (production profile)

Key features:
- Service dependencies with health checks
- Volume mounts for persistence
- Environment variables for configuration
- Health check endpoints for each service
- Network isolation
- Development and production profiles
- Optional services (pgAdmin, Nginx)

#### 4. **nginx.conf** (180 lines)
Production-grade Nginx configuration:
- **SSL/TLS support**: HTTPS with strong ciphers
- **Security headers**: HSTS, CSP, X-Frame-Options, etc.
- **Rate limiting**: Protection against abuse
- **Compression**: GZIP for faster delivery
- **WebSocket support**: For Streamlit real-time features
- **Proxy configuration**: Optimized upstream settings
- **Static file caching**: Performance optimization

### Documentation Files

#### 5. **DOCKER_DEPLOYMENT.md** (500 lines)
Comprehensive deployment guide covering:
- Prerequisites and system requirements
- Development environment setup
- Production deployment procedures
- SSL/TLS certificate configuration
- Database management and backups
- Health checks and monitoring
- Troubleshooting common issues
- Security best practices
- Performance optimization
- Maintenance schedules

#### 6. **DEPLOYMENT_CHECKLIST.md** (400 lines)
10-phase pre-deployment checklist:
1. Pre-Deployment Planning
2. Code Preparation
3. Infrastructure Setup
4. Security Hardening
5. Application Deployment
6. Monitoring & Alerting
7. Documentation
8. Knowledge Transfer & Training
9. Go-Live
10. Post-Deployment

Features:
- Sign-off checkpoints at each phase
- Detailed verification steps
- Security verification items
- Post-deployment verification
- Incident response procedures
- Rollback instructions
- Team contacts and escalation paths

### CI/CD Files

#### 7. **.github/workflows/deploy.yml** (300 lines)
GitHub Actions workflow with 7 jobs:

1. **build** (Build & Test)
   - Multi-service Docker builds (dashboard, api)
   - Matrix strategy for parallel builds
   - Container registry push (GitHub Container Registry)
   - Image testing and validation

2. **security** (Security Scan)
   - Trivy vulnerability scanning
   - Dependency security checks
   - SARIF report upload to GitHub Security

3. **quality** (Code Quality)
   - Linting with flake8
   - Code formatting with black
   - Import sorting with isort
   - Pylint on critical modules

4. **deploy-staging** (Deploy to Staging)
   - Triggered on `develop` branch
   - SSH deployment to staging server
   - Health check verification
   - Slack notifications

5. **deploy-production** (Deploy to Production)
   - Triggered on `main` branch (requires approval)
   - GitHub deployment tracking
   - Production health checks
   - Smoke test execution
   - Comprehensive Slack notifications

6. **docs** (Generate Documentation)
   - API documentation with pdoc3
   - Static site generation with mkdocs
   - GitHub Pages deployment

7. **cleanup** (Cleanup)
   - Docker image pruning
   - Build artifact removal

Features:
- Automatic deployments on branch push
- Manual workflow dispatch for emergency deployments
- Environment-based deployment (development, staging, production)
- Concurrent job execution for speed
- Conditional deployment based on branch/event
- Secret management for sensitive data
- Comprehensive logging and notifications

---

## Getting Started

### Development Setup

```bash
# Clone repository
git clone <repository>
cd Financial\ Risk\ Analysis\ and\ Hybrid\ Fraud\ Detection\ System

# Copy environment template
cp .env.dashboard.template .env.dashboard

# Start all services
docker-compose -f docker-compose.dashboard.yml up

# Services available at:
# - Dashboard: http://localhost:8501
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Database: localhost:5432 (psql -h localhost -U postgres)
# - Redis: localhost:6379
# - pgAdmin: http://localhost:5050
```

### Production Deployment

```bash
# Create production environment file
cp .env.dashboard.template .env.dashboard.prod

# Configure environment variables
# Edit .env.dashboard.prod with production values

# Build and deploy with production profile
docker-compose -f docker-compose.dashboard.yml \
  --env-file .env.dashboard.prod \
  --profile production \
  up -d

# Verify services
docker-compose -f docker-compose.dashboard.yml ps
docker-compose -f docker-compose.dashboard.yml logs
```

---

## Architecture

### Multi-Container Stack

```
┌─────────────────────────────────────────────────────┐
│                    Internet (Users)                 │
└──────────────────────────┬──────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Nginx      │  (SSL/TLS, Rate Limiting)
                    │  Port 80/443│
                    └──────┬──────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
    ┌───▼────────┐               ┌──────────▼────┐
    │ Streamlit  │               │    FastAPI    │
    │ Dashboard  │               │    Backend    │
    │ Port 8501  │               │   Port 8000   │
    └───┬────────┘               └──────┬────────┘
        │                              │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴─────────────┐
        │                            │
    ┌───▼────────┐         ┌────────▼─────┐
    │ PostgreSQL │         │    Redis     │
    │ Port 5432  │         │  Port 6379   │
    └────────────┘         └──────────────┘

    [Optional Services]
    ├─ pgAdmin (Port 5050) - Database Management
    └─ Nginx Production (Port 80/443) - Reverse Proxy
```

### Data Flow

1. **User Access**: Browser connects to Nginx (HTTPS)
2. **Authentication**: Streamlit validates JWT token
3. **API Calls**: Dashboard makes API requests to FastAPI
4. **Database**: FastAPI queries PostgreSQL
5. **Caching**: Redis stores frequent queries
6. **Response**: Data flows back through reverse proxy

---

## Key Features

### Security
- ✅ Non-root container execution
- ✅ SSL/TLS encryption (HTTPS)
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ Rate limiting and DDoS protection
- ✅ JWT token validation
- ✅ Health checks for availability monitoring

### Performance
- ✅ Multi-stage Docker builds (optimized image size)
- ✅ GZIP compression
- ✅ Static file caching
- ✅ Redis caching layer
- ✅ Database connection pooling
- ✅ Load balancing with Nginx

### Reliability
- ✅ Health check endpoints
- ✅ Container restart policies
- ✅ Database persistence
- ✅ Automated backups
- ✅ Monitoring and alerting
- ✅ Graceful shutdown handling

### Operations
- ✅ Environment-based configuration
- ✅ Comprehensive logging
- ✅ Docker volume management
- ✅ Network isolation
- ✅ Service health monitoring
- ✅ Easy scaling capabilities

---

## Configuration

### Environment Variables

**Dashboard Configuration** (.env.dashboard):
```env
API_BASE_URL=http://api:8000
SESSION_TIMEOUT_MINUTES=15
DEBUG_MODE=false
STREAMLIT_SERVER_HEADLESS=true
```

**Backend Configuration**:
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/fraud_db
JWT_SECRET_KEY=<secure-random-key>
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
```

**Security Settings**:
```env
POSTGRES_PASSWORD=<strong-password>
JWT_EXPIRATION_HOURS=24
MAX_LOGIN_ATTEMPTS=5
```

### Volume Mounts

- **`postgres_data`**: Database persistence
- **`redis_data`**: Cache persistence
- **`./dashboard`**: Dashboard code (development)
- **`./backend`**: Backend code (development)

---

## Deployment Workflows

### Development Workflow

```
Developer Push
    ↓
Git Webhook Trigger
    ↓
GitHub Actions: Build & Test
    ↓
Publish to Registry (skipped for PR)
    ↓
Staging Auto-Deploy (develop branch)
    ↓
Smoke Tests
    ↓
Team Notification
```

### Production Workflow

```
Code Review & Approval
    ↓
Merge to main
    ↓
GitHub Actions Triggered
    ↓
Build & Test & Security Scan
    ↓
Code Quality Checks
    ↓
Manual Approval Required
    ↓
Deploy to Production
    ↓
Health Checks & Smoke Tests
    ↓
Documentation Generation
    ↓
Notifications to Team
```

### Manual Emergency Deployment

```
Workflow Dispatch Trigger
    ↓
Select Environment (dev/staging/prod)
    ↓
Same Build & Test Pipeline
    ↓
Direct Deployment
    ↓
Monitoring & Alerts
```

---

## Monitoring & Observability

### Health Checks

Each service has health check endpoints:

```bash
# Streamlit Dashboard
curl http://localhost:8501/_stcore/health

# FastAPI Backend
curl http://localhost:8000/health

# PostgreSQL Database
docker-compose exec db pg_isready -U postgres

# Redis Cache
docker-compose exec redis redis-cli ping
```

### Container Status

```bash
# View all services
docker-compose ps

# View resource usage
docker stats

# View logs for specific service
docker-compose logs -f dashboard

# View logs for all services
docker-compose logs -f
```

### Performance Metrics

The Nginx configuration collects:
- Request latency
- Response size
- Cache hit/miss ratio
- Error rates (4xx, 5xx)
- Upstream health

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Verify ports available
sudo lsof -i :8000 -i :8501 -i :5432

# Check resource limits
df -h  # Disk space
free -h  # Memory
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec db psql -U postgres -d fraud_db

# Check service status
docker-compose ps db

# View database logs
docker-compose logs db
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check database queries
docker-compose exec db psql -U postgres -d fraud_db \
  -c "SELECT * FROM pg_stat_statements"

# Monitor Redis
docker-compose exec redis redis-cli info stats
```

---

## Scaling

### Horizontal Scaling

For production, use Kubernetes or container orchestration:

```yaml
# Example: 3 dashboard instances + load balancer
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fraud-dashboard
  template:
    metadata:
      labels:
        app: fraud-dashboard
    spec:
      containers:
      - name: dashboard
        image: ghcr.io/org/repo/dashboard:latest
        ports:
        - containerPort: 8501
```

### Vertical Scaling

Increase resource limits in docker-compose.yml:

```yaml
services:
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Security Hardening

### Network Security
- Run services on isolated Docker network
- Only expose necessary ports to host
- Use firewall rules on host

### Application Security
- Rotate secrets regularly
- Use strong passwords (min 32 chars)
- Enable HTTPS only
- Implement rate limiting
- Keep dependencies updated

### Data Security
- Enable database encryption
- Configure backup encryption
- Use TLS for database connections
- Monitor access logs

---

## Maintenance

### Regular Tasks

**Daily**: Monitor error logs, check backups

**Weekly**: Review metrics, update dependencies

**Monthly**: Security patches, capacity planning

**Quarterly**: Disaster recovery drill, security audit

### Backup & Recovery

```bash
# Backup database
docker-compose exec -T db pg_dump -U postgres fraud_db | gzip > backup.sql.gz

# Restore database
cat backup.sql.gz | gunzip | docker-compose exec -T db psql -U postgres fraud_db

# Backup volumes
docker run --rm -v fraud_network_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## Support & Documentation

- **Deployment Guide**: See DOCKER_DEPLOYMENT.md
- **Deployment Checklist**: See DEPLOYMENT_CHECKLIST.md
- **Dashboard Documentation**: See dashboard/README.md
- **Testing Guide**: See DASHBOARD_TESTING.md

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial release with Docker, docker-compose, Nginx, CI/CD |

---

## License

This deployment infrastructure is part of the Financial Risk Analysis and Hybrid Fraud Detection System.

---

## Questions?

Refer to DOCKER_DEPLOYMENT.md for detailed troubleshooting and common issues.
