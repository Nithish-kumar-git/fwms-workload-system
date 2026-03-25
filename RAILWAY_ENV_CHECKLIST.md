# Railway Environment Variables Checklist

## Root Cause
Railway backend returns 503 because the Python app crashes on import when `app/core/config.py` tries to instantiate `Settings()` with missing/invalid environment variables.

## Required Environment Variables

Check Railway dashboard and ensure these are set:

### 1. DATABASE_URL (CRITICAL)
```
postgresql://user:password@host:port/database
```
- Railway should auto-provide this if you have a PostgreSQL service attached
- Check: Railway Dashboard → Your Service → Variables tab
- Look for: `DATABASE_URL` variable

### 2. SECRET_KEY (CRITICAL)
```
SECRET_KEY=<minimum-32-character-random-string>
```
- Must be at least 32 characters
- Generate with: `openssl rand -hex 32`
- Example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

### 3. GOOGLE_CLIENT_ID (CRITICAL)
```
GOOGLE_CLIENT_ID=866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com
```
- Use the same value from .env file (shown above)

### 4. GOOGLE_CLIENT_SECRET (CRITICAL)
```
GOOGLE_CLIENT_SECRET=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
```
- Use the same value from .env file (shown above)

### 5. GOOGLE_REDIRECT_URI (CRITICAL)
```
GOOGLE_REDIRECT_URI=https://fwms-workload-system-production.up.railway.app/api/auth/callback
```
- Must match your Railway domain
- Change from `http://localhost:8000` to your Railway URL

### 6. ENV (CRITICAL)
```
ENV=production
```
- Set to `production` for Railway deployment

### 7. SESSION_COOKIE_SECURE (CRITICAL for production)
```
SESSION_COOKIE_SECURE=true
```
- Must be `true` in production (HTTPS)

### 8. DEV_AUTH_BYPASS (CRITICAL - must be false)
```
DEV_AUTH_BYPASS=false
```
- MUST be `false` in production
- App will refuse to start if `true` in production

### 9. SESSION_BACKEND (OPTIONAL)
```
SESSION_BACKEND=memory
```
- Can be `memory` for now (sessions lost on restart)
- TODO: Set to `redis` later with REDIS_URL

### 10. PORT (AUTO-PROVIDED by Railway)
```
PORT=<railway-assigned-port>
```
- Railway auto-provides this
- Do NOT set manually

## How to Set Variables on Railway

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Select your project: "fwms-workload-system-production"
3. Click on your service (backend)
4. Click "Variables" tab
5. Click "New Variable" for each missing variable
6. Click "Deploy" after adding all variables

## Verification Steps

After setting all variables:

1. Wait 2-3 minutes for Railway to redeploy
2. Test health endpoint:
   ```bash
   curl https://fwms-workload-system-production.up.railway.app/health
   ```
3. Should return: `{"status":"healthy"}`

## If Still 503 After Setting Variables

Check Railway deployment logs:
1. Railway Dashboard → Your Service → Deployments tab
2. Click latest deployment
3. Click "View Logs"
4. Look for Python traceback showing exact error

## Next Steps After Railway is Up

1. Restore startup.sh in Dockerfile CMD:
   ```dockerfile
   CMD ["sh", "startup.sh"]
   ```
   This will enable:
   - Database connection check
   - Python import validation (app/startup_check.py)
   - All 22 migrations
   
2. Push to trigger redeploy with migrations:
   ```bash
   git add Dockerfile
   git commit -m "Restore startup.sh with import check and migrations"
   git push origin main
   ```

3. Test full flow in browser:
   - HOD login: https://fwms-workload-system-production.up.railway.app/api/auth/dev-login/16
   - Coordinator login: https://fwms-workload-system-production.up.railway.app/api/auth/dev-login/22
   - Create cycle, test allocation, generate reports
