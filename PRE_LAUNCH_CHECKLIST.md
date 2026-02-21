# Pre-Launch Checklist

Complete all items before opening the system to faculty.

## Infrastructure

- [ ] VPS provisioned (Ubuntu 22.04, 2+ GB RAM)
- [ ] Domain DNS A record pointing to VPS IP
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured: only ports 22, 80, 443 open
- [ ] SSH key auth enabled, password auth disabled

## Configuration

- [ ] `.env.prod` created from `.env.production` template
- [ ] `ENV=production` is set
- [ ] `POSTGRES_PASSWORD` is a strong random password (not default)
- [ ] `SECRET_KEY` generated with `secrets.token_urlsafe(48)` (min 32 chars)
- [ ] `DEV_AUTH_BYPASS=false` confirmed
- [ ] `SESSION_BACKEND=redis` confirmed
- [ ] `SESSION_COOKIE_SECURE=true` confirmed
- [ ] `RATE_LIMIT_ENABLED=true` confirmed

## Google OAuth

- [ ] Google Cloud project created
- [ ] OAuth 2.0 credentials created (Web application type)
- [ ] Authorized redirect URI set to `https://YOUR_DOMAIN/api/auth/callback`
- [ ] OAuth consent screen set to **Internal** (organization only)
- [ ] `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env.prod`
- [ ] `GOOGLE_REDIRECT_URI` matches the authorized redirect URI exactly

## SSL/TLS

- [ ] SSL certificate obtained via certbot
- [ ] `nginx.conf` updated with correct domain name
- [ ] HTTPS redirect working (HTTP → HTTPS)
- [ ] Certificate auto-renewal configured (certbot container running)

## Database

- [ ] Schema migration applied (via Docker init scripts)
- [ ] Seed data loaded (003_seed_minimal.sql)
- [ ] Staff table populated with real faculty emails
- [ ] Coordinator role assigned to correct staff members
- [ ] Database backup procedure tested

## Application Verification

- [ ] `docker compose -f docker-compose.prod.yml ps` — all services healthy
- [ ] `curl https://YOUR_DOMAIN/health` — returns `{"status": "ok"}`
- [ ] `curl https://YOUR_DOMAIN/health/metrics` — returns valid metrics
- [ ] `/api/auth/login` — returns Google authorization URL
- [ ] OAuth login flow tested with a real `@hindustanuniv.ac.in` account
- [ ] Logout tested — session invalidated server-side
- [ ] Coordinator endpoints tested with coordinator account
- [ ] Rate limiting tested — 429 returned after exceeding limit

## Security Final Check

- [ ] `/docs`, `/redoc`, `/openapi.json` return 404 (blocked by Nginx)
- [ ] PostgreSQL port 5432 NOT exposed externally
- [ ] Redis port 6379 NOT exposed externally
- [ ] No `CHANGE_ME` or `placeholder` values in `.env.prod`
- [ ] Docker logs show no `DEV_AUTH_BYPASS` warnings
- [ ] `X-Frame-Options`, `X-Content-Type-Options` headers present in responses
