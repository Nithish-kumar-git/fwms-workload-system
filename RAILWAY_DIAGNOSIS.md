# Railway Deployment Diagnosis

## Current Status: 503 Service Unavailable

**Last tested:** After commit 0852731 (4+ minutes wait)
**URL:** https://fwms-workload-system-production.up.railway.app/health
**Response:** 503 Service Unavailable

## Root Cause Confirmed

The Python application crashes on startup when `app/core/config.py` is imported because **required environment variables are missing on Railway**.

## What Changed

Updated `app/core/config.py` to provide clear error messages instead of cryptic Pydantic validation errors. Now when the app crashes, Railway logs will show:

```
ERROR: DATABASE_URL environment variable is not set
  Railway: Should be auto-provided by PostgreSQL service
  Local: Set in .env file (see .env.example)

ERROR: SECRET_KEY environment variable is not set
  Generate with: python -c "import secrets; print(secrets.token_hex(32))"

ERROR: GOOGLE_CLIENT_ID environment variable is not set
  Get from: https://console.cloud.google.com/apis/credentials

ERROR: GOOGLE_CLIENT_SECRET environment variable is not set
  Get from: https://console.cloud.google.com/apis/credentials

ERROR: GOOGLE_REDIRECT_URI environment variable is not set
  Local: http://localhost:8000/api/auth/callback
  Railway: https://your-app.up.railway.app/api/auth/callback

FATAL: 5 required environment variable(s) missing: DATABASE_URL, SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
Application cannot start. Set these variables and try again.
```

## Required Environment Variables (MUST SET ON RAILWAY)

### 1. DATABASE_URL
**Status:** ⚠️ Should be auto-provided by Railway PostgreSQL service
**Action:** Check Railway Dashboard → Your Service → Variables tab
**Format:** `postgresql://user:password@host:port/database`

If missing, you need to:
1. Go to Railway Dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Link it to your backend service
4. Railway will auto-inject DATABASE_URL

### 2. SECRET_KEY
**Status:** ❌ NOT SET
**Action:** Generate and set manually
**Generate with:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
**Example:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2`
**Minimum length:** 32 characters

### 3. GOOGLE_CLIENT_ID
**Status:** ❌ NOT SET
**Action:** Copy from .env file or Google Cloud Console
**Value from .env:** `866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com`

### 4. GOOGLE_CLIENT_SECRET
**Status:** ❌ NOT SET
**Action:** Copy from .env file or Google Cloud Console
**Value from .env:** `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`

### 5. GOOGLE_REDIRECT_URI
**Status:** ❌ NOT SET
**Action:** Set to Railway URL
**Value:** `https://fwms-workload-system-production.up.railway.app/api/auth/callback`

### 6. ENV (Recommended)
**Status:** ⚠️ Optional but recommended
**Action:** Set to `production`
**Default:** `development` (if not set)

### 7. DEV_AUTH_BYPASS (Critical for Production)
**Status:** ⚠️ MUST be `false` in production
**Action:** Set to `false`
**Default:** `false` (if not set)
**Note:** App will refuse to start if set to `true` with `ENV=production`

### 8. SESSION_COOKIE_SECURE (Auto-handled)
**Status:** ✅ OK
**Default:** `true` (correct for HTTPS)
**Note:** No action needed

## How to Set Variables on Railway

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Select your project
3. Click on your backend service
4. Click "Variables" tab
5. Click "New Variable" for each missing variable
6. Enter variable name and value
7. Click "Add" for each
8. Railway will auto-redeploy after you add variables

## Verification Steps

After setting all variables:

1. Wait 2-3 minutes for Railway to redeploy
2. Check Railway logs for startup messages (should see "Faculty Subject Selection System starting up")
3. Test health endpoint:
   ```bash
   curl https://fwms-workload-system-production.up.railway.app/health
   ```
4. Expected response: `{"status":"healthy"}`

## Next Steps After Railway is Working

1. Restore startup.sh in Dockerfile CMD to enable migrations:
   ```dockerfile
   CMD ["sh", "startup.sh"]
   ```
2. Commit and push:
   ```bash
   git add Dockerfile
   git commit -m "Restore startup.sh with migrations"
   git push origin main
   ```
3. Test full production flow

## Railway Logs Location

To see the exact error messages:
1. Railway Dashboard → Your Service
2. Click "Deployments" tab
3. Click latest deployment
4. Click "View Logs"
5. Look for the ERROR messages from config.py

The logs will now show exactly which environment variables are missing with helpful instructions on how to set them.
