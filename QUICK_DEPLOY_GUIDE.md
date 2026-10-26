# Quick Start: Deploy to Another System

## What You Have
- **Financial Risk Analysis & Hybrid Fraud Detection System**
- Multi-component application:
  - FastAPI Backend (Python)
  - Streamlit Dashboard
  - MySQL Database
  - Redis Cache

---

## 3 Ways to Deploy

### 🐳 **Option 1: Docker Compose (Easiest - Recommended)**

**Time Required**: 15-20 minutes  
**Skill Level**: Beginner

```bash
# Step 1: Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Step 2: Clone the repository
git clone <your-repo-url> fraud-detection
cd fraud-detection

# Step 3: Run deployment script
# On Linux/macOS:
chmod +x deploy.sh
./deploy.sh

# On Windows (PowerShell):
.\deploy.ps1
```

**That's it!** Your application will be:
- ✅ API: http://localhost:8000
- ✅ Dashboard: http://localhost:8501
- ✅ Database configured and populated

---

### 🖥️ **Option 2: Native Installation (More Control)**

**Time Required**: 30-45 minutes  
**Skill Level**: Intermediate

**Prerequisites:**
- Python 3.14+
- MySQL 8.0
- Redis (optional)
- Git

**Steps:**
```bash
# 1. Clone repository
git clone <your-repo-url> fraud-detection
cd fraud-detection

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dashboard.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Initialize database
python run_migrations.py
python seed_database.py

# 6. Start services (in separate terminals)
python run.py                          # Terminal 1: API
streamlit run dashboard/app.py         # Terminal 2: Dashboard
```

---

### ☁️ **Option 3: Cloud Deployment (AWS/Azure)**

**Time Required**: 1-2 hours  
**Skill Level**: Advanced

See: `DEPLOYMENT_TO_ANOTHER_SYSTEM.md` → **Option 3: Cloud Deployment**

Popular options:
- AWS ECS + RDS + ElastiCache
- Azure Container Instances + Azure Database
- Kubernetes (on any cloud)

---

## Verification

After deployment, verify everything works:

```bash
# 1. Check API is running
curl http://localhost:8000/health

# 2. Check Dashboard
# Open browser: http://localhost:8501

# 3. Check Database
# MySQL at localhost:3307

# 4. View logs
docker-compose logs -f  # If using Docker

# 5. Run tests
pytest tests/
```

---

## Common Setup Issues & Fixes

### "Docker command not found"
```bash
# Install Docker Desktop from: https://www.docker.com/products/docker-desktop
# Restart your terminal after installation
```

### "Port 8000 already in use"
```bash
# Find what's using the port:
# Linux/macOS: lsof -i :8000
# Windows: netstat -ano | findstr :8000

# Change port in .env:
API_PORT=8001
```

### "Database connection refused"
```bash
# Make sure MySQL is running:
docker-compose ps mysql  # Should show "Up (healthy)"

# Or check credentials in .env match docker-compose.yml
```

### "Streamlit not found"
```bash
# Install it:
pip install streamlit

# Or reinstall all requirements:
pip install -r requirements-dashboard.txt
```

---

## After Deployment: Next Steps

### 1. **Change Default Passwords** ⚠️
```bash
# Edit .env with strong passwords:
MYSQL_ROOT_PASSWORD=your_very_strong_password_here
MYSQL_PASSWORD=another_strong_password_here
SECRET_KEY=random_cryptographic_key
```

### 2. **Set Up Backups**
```bash
# Docker: Backup database daily
docker-compose exec mysql mysqldump -u fraud_user -p fraud_detection > backup_$(date +%Y%m%d).sql

# Or: Use automated backup script in `/scripts/backup.sh`
```

### 3. **Enable SSL/TLS** (For Production)
```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update docker-compose.yml to use HTTPS
```

### 4. **Set Up Monitoring**
```bash
# Monitor services
docker-compose stats

# View logs
docker-compose logs -f
```

---

## File Guide

| File | Purpose |
|------|---------|
| `DEPLOYMENT_TO_ANOTHER_SYSTEM.md` | Comprehensive deployment guide with all 3 options |
| `SYSTEM_MIGRATION_CHECKLIST.md` | Detailed migration checklist with rollback plan |
| `deploy.sh` | Automated deployment script for Linux/macOS |
| `deploy.ps1` | Automated deployment script for Windows |
| `docker-compose.yml` | Docker Compose configuration |
| `Dockerfile.api` | API container definition |
| `.env.example` | Environment variables template |

---

## Troubleshooting

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f mysql
docker-compose logs -f dashboard
```

### Health Check
```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/api/v1/health/db

# Full system
curl http://localhost:8000/api/v1/health/system
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api

# Full restart (safer)
docker-compose down
docker-compose up -d
```

### Check Disk Space
```bash
# Linux/macOS
df -h

# Windows
Get-Volume

# If running low on space, Docker images can be large
docker system prune  # Clean up unused images
```

---

## System Requirements

### Minimum
- OS: Linux, macOS, or Windows 10+
- CPU: 2+ cores
- RAM: 4GB
- Disk: 5GB
- Network: 50Mbps

### Recommended
- OS: Ubuntu 22.04+ / macOS 12+ / Windows 11
- CPU: 4+ cores
- RAM: 8GB
- Disk: 20GB
- Network: 100Mbps+

---

## Support Resources

1. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **Dashboard**
   - http://localhost:8501

3. **Documentation Files**
   - `DEPLOYMENT_TO_ANOTHER_SYSTEM.md` - Full guide
   - `SYSTEM_MIGRATION_CHECKLIST.md` - Migration steps
   - `OPERATIONS_RUNBOOK.md` - Daily operations
   - `DEPLOYMENT_GUIDE.md` - Detailed procedures

4. **Logs**
   - Docker: `docker-compose logs -f`
   - MySQL: Check container logs
   - Application: See `/logs` directory

---

## Complete Migration Timeline

| Phase | Duration | Steps |
|-------|----------|-------|
| **Preparation** | 1-2 hrs | Backup, plan, test |
| **Setup** | 30-60 min | Install Docker, clone repo |
| **Configuration** | 15-30 min | Set .env, build images |
| **Deployment** | 5-10 min | Start services |
| **Testing** | 30-60 min | Health checks, run tests |
| **Optimization** | 1-2 hrs | Performance tuning, monitoring |
| **Total** | **4-7 hours** | Full production-ready deployment |

---

## One-Command Deployment (Docker)

If everything is ready:
```bash
git clone <repo> && cd fraud-detection && docker-compose up -d && sleep 30 && docker-compose exec api python seed_database.py && echo "✅ Ready! http://localhost:8000"
```

---

## Security Checklist ✓

Before going to production:
- [ ] Changed all default passwords
- [ ] Generated secure SECRET_KEY
- [ ] Enabled SSL/TLS certificates
- [ ] Set ENVIRONMENT=production
- [ ] Disabled DEBUG mode
- [ ] Configured firewall rules
- [ ] Set up backups
- [ ] Verified database encryption
- [ ] Enabled API authentication
- [ ] Set up monitoring/alerts

---

## Getting Help

**If something doesn't work:**

1. Check logs: `docker-compose logs -f`
2. See `SYSTEM_MIGRATION_CHECKLIST.md` → Troubleshooting section
3. Check API docs: http://localhost:8000/docs
4. Review `DEPLOYMENT_GUIDE.md` for detailed instructions

**Still stuck?** Check:
- `.env` configuration is correct
- All ports are available
- Docker is running
- System has enough disk space
- Internet connection is stable

---

**Status**: ✅ Ready to Deploy  
**Last Updated**: October 2024  
**Application Version**: 1.0.0
