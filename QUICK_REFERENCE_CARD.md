# 🎯 DEPLOYMENT QUICK REFERENCE CARD

## Three Deployment Options at a Glance

### ⚡ OPTION 1: AUTOMATIC (15 min) - EASIEST
```bash
# Linux/macOS
git clone <repo> fraud-detection && cd fraud-detection
chmod +x deploy.sh && ./deploy.sh

# Windows PowerShell
git clone <repo> fraud-detection
cd fraud-detection
.\deploy.ps1
```
**Result**: Fully automated, all services running  
**Read**: QUICK_DEPLOY_GUIDE.md → Option 1

---

### 📖 OPTION 2: GUIDED (30 min) - LEARN
1. Read: [QUICK_DEPLOY_GUIDE.md](./QUICK_DEPLOY_GUIDE.md)
2. Read: [DEPLOYMENT_TO_ANOTHER_SYSTEM.md](./DEPLOYMENT_TO_ANOTHER_SYSTEM.md)
3. Follow step-by-step instructions
4. Test with: `curl http://localhost:8000/health`

**Result**: Full understanding, complete control

---

### 🏢 OPTION 3: PRODUCTION (4-7 hrs) - ENTERPRISE
1. Read: [SYSTEM_MIGRATION_CHECKLIST.md](./SYSTEM_MIGRATION_CHECKLIST.md)
2. Execute: 7-phase migration plan
3. Backup, test, and verify each phase
4. Security hardening & monitoring setup

**Result**: Production-ready with backup/rollback plan

---

## After Deployment - Access Points

| Component | URL/Port |
|-----------|----------|
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Dashboard** | http://localhost:8501 |
| **Database** | localhost:3307 |
| **Redis** | localhost:6379 |

---

## Essential Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health

# Run tests
docker-compose exec api pytest

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Get shell access
docker-compose exec api bash
```

---

## What Gets Deployed

✅ **FastAPI Backend** - REST API with fraud detection  
✅ **Streamlit Dashboard** - Interactive analytics UI  
✅ **MySQL Database** - With schema and sample data  
✅ **Redis Cache** - Performance optimization  

---

## System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| OS | Linux/macOS/Windows 10+ | Ubuntu 22.04+ / macOS 12+ / Windows 11 |
| CPU | 2 cores | 4 cores |
| RAM | 4GB | 8GB+ |
| Disk | 5GB | 20GB+ |

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Docker not found | Install from https://docker.com |
| Port 8000 in use | Edit `.env`: `API_PORT=8001` |
| DB connection fails | Wait 30s for MySQL to start |
| Out of memory | Increase Docker memory to 4GB+ |
| Streamlit not found | `pip install streamlit` |

---

## Pre-Deployment Checklist

- [ ] Docker Desktop installed
- [ ] Git installed
- [ ] 5GB+ disk space
- [ ] 4GB+ RAM
- [ ] Repository cloned
- [ ] `.env` configured
- [ ] Ports 8000, 8501, 3307 available

---

## Post-Deployment Checklist

- [ ] API responds: `curl http://localhost:8000/health`
- [ ] Dashboard loads: http://localhost:8501
- [ ] Database has data: Check MySQL
- [ ] Tests pass: `docker-compose exec api pytest`
- [ ] Logs clean: `docker-compose logs`
- [ ] Changed default passwords
- [ ] Backed up database

---

## Security Must-Do

```env
# Edit .env with STRONG values:
MYSQL_PASSWORD=YourVerySecurePassword123!@#
MYSQL_ROOT_PASSWORD=AnotherSecurePassword456!@#
SECRET_KEY=GeneratedWithSecretsModule
ENVIRONMENT=production
DEBUG=False
```

---

## File Map

| File | Purpose | When to Use |
|------|---------|------------|
| START_HERE_DEPLOYMENT_SUMMARY.md | Overview | Always read first |
| QUICK_DEPLOY_GUIDE.md | Fast start | For 15-30 min deployment |
| DEPLOYMENT_TO_ANOTHER_SYSTEM.md | Complete guide | For all 3 methods |
| SYSTEM_MIGRATION_CHECKLIST.md | Production plan | For enterprise deployment |
| DEPLOYMENT_INDEX_COMPLETE.md | Navigation | When lost or need help |
| deploy.sh | Auto Linux/macOS | For automatic deployment |
| deploy.ps1 | Auto Windows | For automatic deployment |

---

## Quick Decision Matrix

| Situation | Choose | Time |
|-----------|--------|------|
| "Fastest deployment" | deploy.sh/.ps1 | 15 min |
| "Learn as I go" | QUICK_DEPLOY_GUIDE.md | 30 min |
| "Complete instructions" | DEPLOYMENT_TO_ANOTHER_SYSTEM.md | 45 min |
| "Production migration" | SYSTEM_MIGRATION_CHECKLIST.md | 4-7 hrs |
| "Need help" | DEPLOYMENT_INDEX_COMPLETE.md | 5 min |

---

## Deployment Flow

```
START
  ↓
[Read appropriate guide]
  ↓
[Configure .env]
  ↓
[Clone repository]
  ↓
[Run deployment]
  ├─ Automatic: ./deploy.sh (15 min)
  ├─ Manual: Follow guide step-by-step (30 min)
  └─ Production: Execute 7-phase plan (4-7 hrs)
  ↓
[Wait for services]
  ↓
[Run health checks]
  ↓
[Change passwords]
  ↓
SUCCESS ✅
```

---

## Support Resources

**Logs & Status**:
```bash
docker-compose ps          # Service status
docker-compose logs -f     # Real-time logs
docker-compose logs -f api # API logs only
```

**Documentation**:
- Quick issues: QUICK_DEPLOY_GUIDE.md
- Detailed help: DEPLOYMENT_TO_ANOTHER_SYSTEM.md
- Troubleshooting: SYSTEM_MIGRATION_CHECKLIST.md
- All topics: DEPLOYMENT_INDEX_COMPLETE.md

**API Help**:
- Interactive: http://localhost:8000/docs
- Alternative: http://localhost:8000/redoc

---

## Useful Links

- Docker: https://docker.com
- Git: https://git-scm.com
- FastAPI: https://fastapi.tiangolo.com
- Streamlit: https://streamlit.io
- MySQL: https://mysql.com

---

## Success Indicators

✅ `docker-compose ps` shows 4 services "Up"  
✅ `curl http://localhost:8000/health` returns 200  
✅ http://localhost:8501 loads dashboard  
✅ No errors in logs  
✅ Tests pass: `docker-compose exec api pytest`  

---

## Next Step: Pick Your Path

1. **15 minutes**: Run `./deploy.sh` or `.\deploy.ps1`
2. **30 minutes**: Read QUICK_DEPLOY_GUIDE.md
3. **4-7 hours**: Read SYSTEM_MIGRATION_CHECKLIST.md

---

**Version**: 1.0.0 | **Status**: ✅ Ready | **Last Updated**: October 2024
