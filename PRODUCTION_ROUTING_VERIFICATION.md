# PRODUCTION ROUTING VERIFICATION

## 🔍 1. CRITICAL CHECK: Where does `/api/auth/login` go in production?

### Evidence from Code:

**File: `frontend/src/pages/LoginPage.tsx` (Line 16)**
```typescript
const res = await fetch('/api/auth/login');
```

**File: `frontend/src/pages/StaffEmailsPage.tsx` (Line 30)**
```typescript
const res = await fetch('/api/admin/staff/emails', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` }
});
```

**File: `frontend/src/api/client.ts` (Lines 4-6)**
```typescript
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';
```

### Answer: Where does `/api/auth/login` go in production?

**❌ VERCEL DOMAIN (FRONTEND ITSELF)**

**Explanation:**
- Direct `fetch('/api/...')` calls use **relative paths**
- Browser resolves relative paths to **same domain as the page**
- In production: `https://fwms-workload-system.vercel.app/api/auth/login`
- This hits **Vercel frontend**, NOT Railway backend
- **Result:** 404 error (frontend has no `/api` routes)

---

## 🔍 2. PROXY / REWRITE PROOF

### A. Local Development Proxy

**File: `frontend/vite.config.ts` (Lines 7-13)**
```typescript
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

**Status:** ✅ PROXY EXISTS
**Scope:** LOCAL DEVELOPMENT ONLY (Vite dev server)
**Behavior:** `/api/*` → `http://localhost:8000`

---

### B. Production Proxy/Rewrite

**File: `vercel.json` (Complete Contents)**
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "echo skip",
  "framework": null
}
```

**Status:** ❌ NO PROXY/REWRITE EXISTS
**Missing:** No `rewrites` array
**Missing:** No `routes` configuration
**Missing:** No `/api` routing to Railway backend

---

### C. Environment Variable Check

**File: `frontend/.env` (Local Development)**
```env
VITE_API_URL=http://localhost:8000
VITE_DEV_MODE=true
```

**File: `frontend/.env.local` (Local Development)**
```env
# VITE_API_URL="" # Commented out for local dev - uses Vite proxy to localhost:8000
VITE_DEV_MODE="true"
```

**Production (Vercel Dashboard):**
- ❌ `VITE_API_URL` is **NOT SET** (needs to be added)
- ❌ Without this, axios client falls back to relative `/api`

---

## 🔍 3. ROUTING ANALYSIS

### Question: Is `/api/*` routed to Railway?

**Answer: NO**

**Evidence:**
1. ❌ `vercel.json` has NO `rewrites` configuration
2. ❌ `vercel.json` has NO `routes` configuration
3. ❌ No proxy exists in production build (Vite proxy is dev-only)
4. ❌ `VITE_API_URL` not set in Vercel environment variables

**Exact Config:**
- **Local Dev:** Vite proxy routes `/api` → `http://localhost:8000` ✅
- **Production:** NO ROUTING ❌

---

## 🔍 4. FINAL VERDICT

### Statement to Verify:
> "No code changes required, only configuration updates."

### Verification Result: **PARTIALLY FALSE**

**Why the original statement was WRONG:**

The system has **TWO DIFFERENT API CALL PATTERNS**:

#### Pattern 1: Axios Client (CONFIGURABLE) ✅
**File:** `frontend/src/api/client.ts`
```typescript
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';
```

**Behavior:**
- IF `VITE_API_URL` is set → uses absolute URL ✅
- IF NOT set → uses relative `/api` ❌

**Used by:** 35+ API endpoints (preferences, allocation, admin, reports, etc.)

**Fix:** Set `VITE_API_URL` in Vercel environment variables (NO CODE CHANGE)

---

#### Pattern 2: Direct fetch() Calls (HARDCODED) ❌
**Files:**
- `frontend/src/pages/LoginPage.tsx` (Line 16)
- `frontend/src/pages/StaffEmailsPage.tsx` (Line 30)

**Code:**
```typescript
fetch('/api/auth/login')
fetch('/api/admin/staff/emails', ...)
```

**Behavior:**
- ALWAYS uses relative path
- IGNORES `VITE_API_URL` environment variable
- CANNOT be configured without code changes

**Fix Required:** CODE CHANGES NEEDED

---

## 📋 CORRECTED STATEMENT

### TRUE Statement:
**"Frontend must use absolute backend URL OR Vercel rewrites for production."**

### Two Solutions:

#### Solution A: Environment Variable + Code Changes (RECOMMENDED)
1. **Set in Vercel:** `VITE_API_URL=https://fwms-workload-system-production.up.railway.app`
2. **Code Changes Required:**
   - Replace `fetch('/api/auth/login')` with axios client call
   - Replace `fetch('/api/admin/staff/emails')` with axios client call
   - OR: Create a helper function that respects `VITE_API_URL`

#### Solution B: Vercel Rewrites (NO CODE CHANGES)
1. **Add to `vercel.json`:**
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
2. **Set in Vercel:** `VITE_API_URL=` (empty or not set, to use relative paths)

---

## ⚠️ CRITICAL FINDINGS

### Issue 1: Direct fetch() Calls Break in Production
**Files Affected:**
- `frontend/src/pages/LoginPage.tsx` (OAuth login)
- `frontend/src/pages/StaffEmailsPage.tsx` (Staff email management)

**Impact:**
- OAuth login completely broken
- Staff email management broken
- These use hardcoded relative paths

**Current Behavior in Production:**
```
fetch('/api/auth/login')
→ https://fwms-workload-system.vercel.app/api/auth/login
→ 404 Not Found (frontend has no /api routes)
```

---

### Issue 2: Axios Client Works IF Configured
**Files Affected:**
- All 35+ API endpoints in `frontend/src/api/client.ts`

**Impact:**
- Will work IF `VITE_API_URL` is set in Vercel
- Will fail if not set (uses relative paths)

**Current Behavior in Production (without VITE_API_URL):**
```
api.get('/preferences/me')
→ baseURL = '/api' (relative)
→ https://fwms-workload-system.vercel.app/api/preferences/me
→ 404 Not Found
```

**Fixed Behavior (with VITE_API_URL set):**
```
api.get('/preferences/me')
→ baseURL = 'https://fwms-workload-system-production.up.railway.app/api'
→ https://fwms-workload-system-production.up.railway.app/api/preferences/me
→ ✅ Works
```

---

## ✅ RECOMMENDED FIX

### Option 1: Code Changes + Environment Variable (CLEANEST)

**Step 1: Replace direct fetch() calls**

**File: `frontend/src/pages/LoginPage.tsx`**
```typescript
// BEFORE (Line 16):
const res = await fetch('/api/auth/login');

// AFTER:
import api from '../api/client';
const res = await api.get('/auth/login');
```

**File: `frontend/src/pages/StaffEmailsPage.tsx`**
```typescript
// BEFORE (Line 30):
const res = await fetch('/api/admin/staff/emails', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` }
});

// AFTER:
import api from '../api/client';
const res = await api.get('/admin/staff/emails');
```

**Step 2: Set Vercel Environment Variable**
```
VITE_API_URL=https://fwms-workload-system-production.up.railway.app
```

**Result:** All API calls use absolute URL, no proxy needed

---

### Option 2: Vercel Rewrites (NO CODE CHANGES)

**File: `vercel.json`**
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

**Result:** All `/api/*` requests proxied to Railway backend

---

## 🎯 FINAL ANSWER

### Question: "Is this statement TRUE or FALSE: 'Frontend must use absolute backend URL instead of /api/...'"

**Answer: TRUE (with clarification)**

**Clarification:**
- **IF using Vercel rewrites:** Can keep relative `/api` paths ✅
- **IF NOT using rewrites:** MUST use absolute backend URL ✅

**Current State:**
- ❌ NO rewrites configured
- ❌ `VITE_API_URL` not set in Vercel
- ❌ Direct fetch() calls use hardcoded relative paths

**Therefore:**
- **TRUE:** Frontend MUST use absolute backend URL
- **OR:** Add Vercel rewrites to proxy `/api/*` to Railway

**Original Claim "No code changes required" is:**
- ✅ TRUE if using Vercel rewrites
- ❌ FALSE if using environment variable only (2 files need changes)

---

## 📊 SUMMARY TABLE

| Component | Current State | Production Behavior | Fix Required |
|-----------|---------------|---------------------|--------------|
| Axios client (35+ endpoints) | Uses `VITE_API_URL` or `/api` | ❌ Calls Vercel (404) | Set `VITE_API_URL` in Vercel |
| LoginPage fetch() | Hardcoded `/api/auth/login` | ❌ Calls Vercel (404) | Code change OR rewrite |
| StaffEmailsPage fetch() | Hardcoded `/api/admin/staff/emails` | ❌ Calls Vercel (404) | Code change OR rewrite |
| Vite proxy | Configured for dev | ✅ Works locally | N/A (dev only) |
| Vercel rewrites | NOT configured | ❌ No routing | Add rewrites OR use env var |

**Verdict:** Code changes ARE required UNLESS Vercel rewrites are added.
