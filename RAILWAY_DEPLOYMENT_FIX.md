# Railway Deployment Fix Summary

## Problem
Railway backend at https://fwms-workload-system-production.up.railway.app/api/health was timing out due to:
1. HEALTHCHECK using hardcoded port 8000 instead of $PORT environment variable
2. HEALTHCHECK using wrong path `/health` instead of `/api/health`
3. Old `cycle_service` imports causing startup failures

## Files Changed: 7

### 1. Dockerfile
**Changes:**
- Fixed HEALTHCHECK to use `$PORT` environment variable instead of hardcoded 8000
- Fixed HEALTHCHECK path from `/health` to `/api/health`
- Added proper Python f-string formatting to read PORT from environment

**Before:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

**After:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/api/health')" || exit 1
```

### 2. app/admin/service.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 573

### 3. app/preference/window_service.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 67

### 4. app/preference/service.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 350

### 5. app/reports/router.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 120

### 6. app/allocation/router.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 96

### 7. app/allocation/service.py
**Changed:** `from app.admin.cycle_service import` → `from app.admin.cycle_service_new import`
**Line:** 467

## Git Commands to Deploy

Run these commands in order:

```bash
# Stage all changes
git add Dockerfile app/admin/service.py app/preference/window_service.py app/preference/service.py app/reports/router.py app/allocation/router.py app/allocation/service.py

# Commit with descriptive message
git commit -m "Fix Railway deployment: update HEALTHCHECK to use PORT env var and fix cycle_service imports"

# Push to trigger Railway redeploy
git push origin main
```

## Expected Result

After Railway redeploys:
- Health check will use the correct PORT (Railway assigns dynamic ports)
- Health check will hit the correct endpoint `/api/health`
- Application will start successfully without import errors
- Backend will be accessible at https://fwms-workload-system-production.up.railway.app/api/health

## Verification

After deployment completes, verify:
1. Railway logs show successful startup
2. Health endpoint responds: `curl https://fwms-workload-system-production.up.railway.app/api/health`
3. No import errors in logs
4. Application is healthy in Railway dashboard
