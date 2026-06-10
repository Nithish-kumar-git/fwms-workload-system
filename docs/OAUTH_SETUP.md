# Google OAuth Setup Instructions

## Current Issue
Google OAuth shows "redirect_uri_mismatch" error because `http://localhost:8000/api/auth/callback` is not registered in Google Cloud Console.

## Fix Steps

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if needed)
3. Navigate to: **APIs & Services** → **Credentials**
4. Find your OAuth 2.0 Client ID (the one with ID: `866513397597-daqoj2v37mm6ko5b3hu9t0rgflupjsi1.apps.googleusercontent.com`)
5. Click on it to edit
6. Under **Authorized redirect URIs**, add:
   - `http://localhost:8000/api/auth/callback` (for local development)
   - `https://your-railway-domain.railway.app/api/auth/callback` (for production)
   - `https://your-vercel-domain.vercel.app/api/auth/callback` (if using Vercel for frontend)
7. Click **Save**

## Alternative: Use Dev Login for Local Development

Since `DEV_AUTH_BYPASS=true` is set in `.env`, you can use the dev login buttons on the login page:
- Click "HOD", "Coordinator", or "Faculty" buttons
- These bypass Google OAuth for local testing

## Production Setup

For production, ensure:
1. `DEV_AUTH_BYPASS=false` in production environment
2. `ENV=production` in production environment  
3. Google OAuth redirect URI matches your production domain
4. `GOOGLE_REDIRECT_URI` environment variable is set correctly
