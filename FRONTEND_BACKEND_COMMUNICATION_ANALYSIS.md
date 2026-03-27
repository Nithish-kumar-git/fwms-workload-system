# FRONTEND-BACKEND COMMUNICATION ANALYSIS

## 🔍 1. FRONTEND API CALL ANALYSIS

### A. Direct fetch() Calls

#### File: `frontend/src/pages/LoginPage.tsx`

**Line 16:**
```typescript
const res = await fetch('/api/auth/login');
```
- **URL:** `/api/auth/login` (relative path)
- **Purpose:** Get Google OAuth authorization URL

**Line 34:**
```typescript
const res = await fetch(`/api/auth/dev-login/${staffId}`, { method: 'POST' });
```
- **URL:** `/api/auth/dev-login/{staffId}` (relative path)
- **Purpose:** Dev-only login bypass

#### File: `frontend/src/pages/StaffEmailsPage.tsx`

**Line 30:**
```typescript
const res = await fetch('/api/admin/staff/emails', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` }
});
```
- **URL:** `/api/admin/staff/emails` (relative path)
- **Purpose:** Get staff emails list

**Line 67:**
```typescript
const res = await fetch(`/api/admin/staff/${editId}/email`, {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email: newEmail })
});
```
- **URL:** `/api/admin/staff/{id}/email` (relative path)
- **Purpose:** Update staff email

### B. Axios API Client

#### File: `frontend/src/api/client.ts`

**Lines 1-11: Base Configuration**
```typescript
import axios from 'axios';

// Construct baseURL: use VITE_API_URL if set, otherwise fallback to relative '/api'
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';

const api = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});
```

**All API Functions (using axios instance):**
- `submitPreference()` → `/preferences`
- `getMyPreferences()` → `/preferences/me`
- `deletePreference()` → `/preferences/{id}`
- `getPreferenceStatus()` → `/preferences/status`
- `runAllocation()` → `/allocation/run`
- `getAdminAllocations()` → `/admin/allocations`
- `overrideAllocation()` → `/admin/allocation/{id}`
- `reassignSubject()` → `/admin/reassign`
- `freezeAllocation()` → `/admin/allocation/freeze`
- `unfreezeAllocation()` → `/admin/allocation/unfreeze`
- `getWorkloadSummary()` → `/admin/workload-summary`
- `getFacultyWorkload()` → `/reports/faculty-workload`
- `getSubjectSummary()` → `/reports/subject-summary`
- `getDepartmentSummary()` → `/reports/department-summary`
- `downloadExcel()` → `/reports/export/workload.xlsx`
- `downloadPdf()` → `/reports/export/workload.pdf`
- `openPrefWindow()` → `/pref-window/open`
- `closePrefWindow()` → `/pref-window/close`
- `getPrefWindowStatus()` → `/pref-window/status`
- `getStaffList()` → `/admin/staff`
- `createStaff()` → `/admin/staff`
- `updateStaff()` → `/admin/staff/{id}`
- `updateStaffEmail()` → `/admin/staff/{id}/email`
- `updateStaffRole()` → `/admin/staff/{id}/role`
- `deactivateStaff()` → `/admin/staff/{id}/deactivate`
- `createCycle()` → `/cycles`
- `activateCycle()` → `/cycles/activate`
- `listCycles()` → `/cycles`
- `getActiveCycle()` → `/cycles/active`
- `getPipelineStatus()` → `/reports/pipeline-status`
- `approveWorkload()` → `/reports/approve-workload`
- `downloadMasterWorkload()` → `/reports/export/master-workload.xlsx`
- `downloadWorkloadPdf()` → `/reports/export/workload.pdf`
- `getCurrentUser()` → `/auth/me`
- `logout()` → `/auth/logout`

**Total API Calls:** 35+ endpoints

---

## 🔍 2. BASE URL CONFIGURATION

### File: `frontend/src/api/client.ts` (Lines 4-6)

```typescript
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';
```

**Logic:**
- IF `VITE_API_URL` is set → use `{VITE_API_URL}/api`
- ELSE → use relative path `/api`

### File: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
VITE_DEV_MODE=true
```

**Current Configuration:**
- `VITE_API_URL` is SET to `http://localhost:8000`
- Therefore, baseURL = `http://localhost:8000/api`

### File: `frontend/.env.local`

```env
# VITE_API_URL="" # Commented out for local dev - uses Vite proxy to localhost:8000
VITE_DEV_MODE="true"
```

**Note:** VITE_API_URL is commented out in .env.local

**Answer:**
- ✅ YES - Base API URL is defined: `http://localhost:8000/api`
- ❌ NOT using relative paths - using absolute URL

---

## 🔍 3. PROXY OR REWRITE CHECK

### File: `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Proxy Configuration:**
- ✅ YES - Proxy is configured
- **Pattern:** `/api` → `http://localhost:8000`
- **changeOrigin:** true
- **Applies to:** Local development only (vite dev server)

### File: `vercel.json`

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "echo skip",
  "framework": null
}
```

**Production Proxy:**
- ❌ NO - No rewrites or proxy configuration for production
- ❌ NO - No `/api` rewrite to backend URL

**Answer:**
- ✅ Local Dev: `/api` proxied to `http://localhost:8000`
- ❌ Production: NO PROXY configured

---

## 🔍 4. BACKEND URL USAGE

### Search Results:

**Railway URL:** `https://fwms-workload-system-production.up.railway.app`

**Searched for:** `railway.app`
- **Result:** NOT FOUND

**Searched for:** `fwms-workload-system`
- **Found in:** `frontend/.vercel/project.json` (Vercel project metadata only)

**Answer:**
- ❌ NOT FOUND - Railway backend URL is NOT used anywhere in frontend code
- ❌ NOT FOUND - No absolute backend URL configured for production

---

## 🔍 5. LOGIN FLOW TRACE

### Step 1: User Clicks "Sign in with Google"

**File:** `frontend/src/pages/LoginPage.tsx` (Line 12-26)

```typescript
const handleGoogleLogin = async () => {
    setError('');
    setLoading('google');
    try {
        const res = await fetch('/api/auth/login');
        const data = await res.json();
        if (data.authorization_url) {
            window.location.href = data.authorization_url;
        } else {
            setError('Could not get Google login URL');
        }
    } catch {
        setError('Failed to connect to server');
    } finally {
        setLoading('');
    }
};
```

**Action:** Calls `/api/auth/login`

### Step 2: Backend Returns Google OAuth URL

**Backend:** `app/auth/router.py` (Line 88-91)

```python
@router.get("/login", response_model=LoginResponse)
async def login():
    """Return Google OAuth authorization URL."""
    url = oauth_client.get_authorization_url()
    return LoginResponse(authorization_url=url)
```

**Returns:** `{"authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..."}`

### Step 3: Frontend Redirects to Google

```typescript
window.location.href = data.authorization_url;
```

**Action:** User redirected to Google consent screen

### Step 4: Google Redirects Back to Backend

**Redirect URI:** `http://localhost:8000/api/auth/callback?code=...`

**Backend:** `app/auth/router.py` (Line 95)

```python
@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(None)):
```

### Step 5: Backend Redirects to Frontend with Token

**Backend:** `app/auth/router.py` (Line 133-134)

```python
frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
resp = RedirectResponse(url=f"{frontend_url}/dashboard?token={auth['token']}", status_code=302)
```

**Redirect:** `http://localhost:5173/dashboard?token=...`

### Step 6: Frontend Captures Token

**File:** `frontend/src/api/client.ts` (Line 26-36)

```typescript
// Capture JWT from OAuth callback redirect (?token=...)
if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
        localStorage.setItem('jwt_token', token);
        params.delete('token');
        const clean = params.toString();
        const newUrl = window.location.pathname + (clean ? `?${clean}` : '');
        window.history.replaceState({}, '', newUrl);
    }
}
```

**Action:** Stores token in localStorage and cleans URL

---

## 🔍 6. CONCLUSION

### Current State:

#### Local Development:
- ✅ Frontend: `http://localhost:5173`
- ✅ Backend: `http://localhost:8000`
- ✅ Vite proxy: `/api` → `http://localhost:8000`
- ✅ VITE_API_URL: `http://localhost:8000` (absolute URL)
- ✅ OAuth callback: `http://localhost:8000/api/auth/callback`
- ✅ Frontend redirect: `http://localhost:5173/dashboard`

**Status:** ✅ WORKING (both proxy and absolute URL configured)

#### Production (Vercel):
- ✅ Frontend: `https://fwms-workload-system.vercel.app` (assumed)
- ✅ Backend: `https://fwms-workload-system-production.up.railway.app`
- ❌ NO proxy configured in vercel.json
- ❌ VITE_API_URL not set in Vercel environment
- ❌ OAuth callback: Still pointing to `http://localhost:8000/api/auth/callback`
- ❌ Frontend redirect: Still pointing to `http://localhost:5173/dashboard`

**Status:** ❌ BROKEN - Frontend will call itself, not backend

---

## 📋 EXACT CHANGES REQUIRED

### 1. Vercel Environment Variables (CRITICAL)

**Add to Vercel Dashboard:**
```
VITE_API_URL=https://fwms-workload-system-production.up.railway.app
VITE_DEV_MODE=false
```

### 2. Railway Environment Variables (CRITICAL)

**Add to Railway Dashboard:**
```
GOOGLE_REDIRECT_URI=https://fwms-workload-system-production.up.railway.app/api/auth/callback
FRONTEND_URL=https://fwms-workload-system.vercel.app
ENV=production
DEV_AUTH_BYPASS=false
```

### 3. Google Cloud Console (CRITICAL)

**Add Authorized Redirect URI:**
```
https://fwms-workload-system-production.up.railway.app/api/auth/callback
```

### 4. Optional: Add Vercel Rewrite (ALTERNATIVE)

**File:** `vercel.json`
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "echo skip",
  "framework": null,
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://fwms-workload-system-production.up.railway.app/api/:path*"
    }
  ]
}
```

**Note:** This is OPTIONAL if VITE_API_URL is set correctly.

---

## ⚠️ CRITICAL FINDINGS

### Issue 1: Frontend Calling Itself in Production
- **Current:** Frontend uses relative `/api` paths OR `VITE_API_URL` if set
- **Problem:** VITE_API_URL not set in Vercel → frontend calls itself
- **Impact:** ALL API calls fail in production

### Issue 2: OAuth Callback Pointing to Localhost
- **Current:** `GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback`
- **Problem:** Google redirects to localhost, not Railway
- **Impact:** OAuth login completely broken in production

### Issue 3: Frontend Redirect Pointing to Localhost
- **Current:** `FRONTEND_URL=http://localhost:5173` (or default)
- **Problem:** After OAuth, backend redirects to localhost
- **Impact:** Users redirected to localhost after login

---

## ✅ VERIFICATION CHECKLIST

Before deploying:
- [ ] VITE_API_URL set in Vercel to Railway backend URL
- [ ] GOOGLE_REDIRECT_URI set in Railway to Railway callback URL
- [ ] FRONTEND_URL set in Railway to Vercel frontend URL
- [ ] Google Cloud Console has Railway callback URL authorized
- [ ] ENV=production in Railway
- [ ] DEV_AUTH_BYPASS=false in Railway
- [ ] Test OAuth flow end-to-end

---

## 🎯 ANSWER TO KEY QUESTIONS

**Is frontend currently calling:**
- ❌ itself (relative /api/...) - NO (has VITE_API_URL set)
- ✅ backend (absolute URL) - YES (in local dev only)
- ❌ backend (in production) - NO (VITE_API_URL not set in Vercel)

**What EXACT change is required:**
1. Set `VITE_API_URL` in Vercel environment variables
2. Set `GOOGLE_REDIRECT_URI` in Railway environment variables
3. Set `FRONTEND_URL` in Railway environment variables
4. Add Railway callback URL to Google Cloud Console

**Status:** READY FOR CONFIGURATION - NO CODE CHANGES NEEDED
