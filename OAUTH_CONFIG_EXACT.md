# GOOGLE OAUTH CONFIGURATION - EXACT LOCATIONS

## 🔍 1. BACKEND CONFIG

### File: `app/core/config.py`

**Line 75-78: OAuth Settings Definition**
```python
    # OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    ALLOWED_EMAIL_DOMAIN: str = "hindustanuniv.ac.in"
```

**Line 81: Frontend URL**
```python
    FRONTEND_URL: str = "http://localhost:5173"
```

**Line 127-128: Config Loading**
```python
    class Config:
        env_file = ".env"
        case_sensitive = True
```

**How values are loaded:**
- Pydantic BaseSettings reads from `.env` file
- Environment variables override .env values
- Required fields: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
- Optional with defaults: ALLOWED_EMAIL_DOMAIN, FRONTEND_URL

---

### File: `app/auth/google_oauth.py`

**Line 30: Token Endpoint**
```python
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
```

**Line 32-36: OAuth Client Initialization**
```python
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.allowed_domain = settings.ALLOWED_EMAIL_DOMAIN
```

**Line 195: Global Instance**
```python
oauth_client = GoogleOAuthClient()
```

---

## 🔍 2. CALLBACK ROUTE

### File: `app/auth/router.py`

**Line 28: Router Prefix**
```python
router = APIRouter(prefix="/api/auth", tags=["auth"])
```

**Line 95: Callback Route Handler**
```python
@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(None)):
```

**Full Path:** `/api/auth/callback`

**Function:** `oauth_callback` (lines 95-149)

**What it does:**
1. Receives `code` parameter from Google
2. Calls `oauth_client.exchange_code_for_token(code)` (line 105)
3. Looks up user in database by email (lines 113-116)
4. Creates JWT token (line 131)
5. Redirects to frontend with token (line 133-134)

---

## 🔍 3. TOKEN EXCHANGE CODE

### File: `app/auth/google_oauth.py`

**Line 71-91: Token Exchange Function**
```python
    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for tokens (standard OAuth 2.0 flow).
        """
        data = urllib.parse.urlencode({
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_response = json.loads(resp.read().decode("utf-8"))
```

**POST Request Details:**
- **URL:** `https://oauth2.googleapis.com/token`
- **Method:** POST
- **Content-Type:** `application/x-www-form-urlencoded`
- **Payload:**
  ```
  code={authorization_code}
  client_id={GOOGLE_CLIENT_ID}
  client_secret={GOOGLE_CLIENT_SECRET}
  redirect_uri={GOOGLE_REDIRECT_URI}
  grant_type=authorization_code
  ```

---

## 🔍 4. FRONTEND LOGIN FLOW

### File: `frontend/src/pages/LoginPage.tsx`

**Line 12-26: Login Button Handler**
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

**URL Used:** `/api/auth/login` (relative path, NOT localhost)
- Frontend uses relative path
- Browser resolves to same domain as frontend
- Backend must be proxied or CORS-enabled

---

## 🔍 5. CURRENT VALUES (RUNTIME)

**From running container:**

```
GOOGLE_CLIENT_ID: 866513397597-daqoj2v...oogleusercontent.com
GOOGLE_REDIRECT_URI: http://localhost:8000/api/auth/callback
FRONTEND_URL: http://localhost:5173
```

**Full values from .env file:**
```env
GOOGLE_CLIENT_ID=866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
FRONTEND_URL=http://localhost:5175
```

**⚠️ MISMATCH DETECTED:**
- .env has `FRONTEND_URL=http://localhost:5175`
- Runtime shows `FRONTEND_URL=http://localhost:5173`
- **Reason:** Container not restarted after .env change OR using default value

---

## 🔍 6. DEPLOYMENT ENV

### Local Development (.env file)

**File:** `.env` (root directory)
```env
GOOGLE_CLIENT_ID=866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
FRONTEND_URL=http://localhost:5175
```

### Railway Deployment

**Status:** MISSING - Not configured in Railway dashboard

**Required Railway Environment Variables:**
```
GOOGLE_CLIENT_ID=866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://your-railway-app.up.railway.app/api/auth/callback
FRONTEND_URL=https://your-vercel-frontend.vercel.app
ENV=production
DEV_AUTH_BYPASS=false
```

**⚠️ CRITICAL:** Railway deployment will FAIL without these variables set in Railway dashboard.

---

## 📋 SUMMARY

### ✅ CONFIGURED
- Backend config structure (app/core/config.py)
- OAuth client implementation (app/auth/google_oauth.py)
- Callback route handler (app/auth/router.py)
- Token exchange code (working)
- Frontend login button (working)
- Local .env file (has values)

### ❌ MISSING
- Railway environment variables (not set in dashboard)
- Production GOOGLE_REDIRECT_URI (needs Railway URL)
- Production FRONTEND_URL (needs Vercel URL)

### ⚠️ ISSUES
- Container using old FRONTEND_URL value (needs rebuild)
- .env has 5175, runtime shows 5173

---

## 🔧 NEXT STEPS

1. **Fix local container:**
   ```bash
   docker-compose down
   docker-compose build app
   docker-compose up -d
   ```

2. **Configure Railway:**
   - Go to Railway dashboard
   - Add environment variables listed above
   - Update GOOGLE_REDIRECT_URI to Railway URL
   - Update FRONTEND_URL to Vercel URL

3. **Update Google Cloud Console:**
   - Add Railway callback URL to authorized redirect URIs
   - Format: `https://your-app.up.railway.app/api/auth/callback`
