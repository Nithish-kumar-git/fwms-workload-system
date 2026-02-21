# VPS Deployment Guide

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Ubuntu 22.04 VPS                │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │  Certbot  │   │  Nginx   │   │   Docker     │ │
│  │ (SSL/TLS) │──▶│ :80/:443 │──▶│   Network    │ │
│  └──────────┘   └──────────┘   │  (backend)   │ │
│                                 │              │ │
│                     ┌───────────┤              │ │
│                     │           │              │ │
│               ┌─────▼─────┐    │              │ │
│               │  FastAPI   │    │              │ │
│               │   :8000    │    │              │ │
│               │ (2 workers)│    │              │ │
│               └──┬──┬──────┘    │              │ │
│                  │  │           │              │ │
│          ┌───────┘  └────────┐  │              │ │
│          │                   │  │              │ │
│   ┌──────▼──────┐   ┌───────▼┐ │              │ │
│   │ PostgreSQL  │   │ Redis  │ │              │ │
│   │    16       │   │   7    │ │              │ │
│   │  :5432      │   │ :6379  │ │              │ │
│   └─────────────┘   └────────┘ └──────────────┘ │
│                                                  │
│  Ports exposed to internet: 80, 443 ONLY         │
└─────────────────────────────────────────────────┘
```

**Traffic flow:** Internet → Nginx (HTTPS) → FastAPI → PostgreSQL/Redis

---

## Prerequisites

- Ubuntu 22.04 LTS VPS (min 2 GB RAM, 20 GB disk)
- Domain name pointing to VPS IP (A record)
- SSH access to VPS

---

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify
docker --version
docker compose version

# Create app directory
sudo mkdir -p /opt/faculty-selection
sudo chown $USER:$USER /opt/faculty-selection
```

---

## Step 2: Upload Project

```bash
# From your local machine
scp -r . user@YOUR_VPS_IP:/opt/faculty-selection/

# Or use git
cd /opt/faculty-selection
git clone YOUR_REPO_URL .
```

---

## Step 3: Configure Environment

```bash
cd /opt/faculty-selection

# Copy production template
cp .env.production .env.prod

# Edit with real values
nano .env.prod
```

**Required values to change:**
| Variable | How to Generate |
|----------|----------------|
| `POSTGRES_PASSWORD` | `openssl rand -base64 32` |
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `GOOGLE_CLIENT_ID` | Google Cloud Console (see Step 4) |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console (see Step 4) |
| `GOOGLE_REDIRECT_URI` | `https://YOUR_DOMAIN/api/auth/callback` |
| `DOMAIN` | Your actual domain name |
| `ADMIN_EMAIL` | Your email for Let's Encrypt |

---

## Step 4: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: `https://YOUR_DOMAIN/api/auth/callback`
7. Copy **Client ID** and **Client Secret** to `.env.prod`

> **Important:** Restrict the OAuth consent screen to your organization's Google Workspace domain (`hindustanuniv.ac.in`) under **OAuth consent screen → User type → Internal**.

---

## Step 5: SSL Certificate (First Time)

```bash
# Replace YOUR_DOMAIN and YOUR_EMAIL
# Create required directories
mkdir -p certbot/www certbot/conf nginx/conf.d

# Get initial certificate (standalone mode)
docker run --rm \
  -p 80:80 \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly \
    --standalone \
    --email YOUR_EMAIL \
    --agree-tos \
    --no-eff-email \
    -d YOUR_DOMAIN

# Update nginx.conf — replace ${DOMAIN} with your actual domain
sed -i "s/\${DOMAIN}/YOUR_DOMAIN/g" nginx/nginx.conf
```

---

## Step 6: Deploy

```bash
cd /opt/faculty-selection

# Build and start all services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f app
```

---

## Step 7: Verify Deployment

```bash
# Health check
curl -s https://YOUR_DOMAIN/health | python3 -m json.tool

# Health metrics (should return status: ok)
curl -s https://YOUR_DOMAIN/health/metrics | python3 -m json.tool

# OAuth login (should redirect to Google)
curl -s https://YOUR_DOMAIN/api/auth/login | python3 -m json.tool
```

---

## Updating

```bash
cd /opt/faculty-selection

# Pull latest code
git pull origin main

# Rebuild and restart (zero-downtime not supported — brief outage expected)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Verify
docker compose -f docker-compose.prod.yml ps
```

---

## Backup

```bash
# Database backup
docker exec faculty_db pg_dump -U faculty_user faculty_selection > backup_$(date +%Y%m%d).sql

# Restore
cat backup_YYYYMMDD.sql | docker exec -i faculty_db psql -U faculty_user faculty_selection
```

---

## Troubleshooting

| Issue | Command |
|-------|---------|
| App won't start | `docker compose -f docker-compose.prod.yml logs app` |
| DB connection error | `docker exec faculty_db pg_isready -U faculty_user` |
| Redis error | `docker exec faculty_redis redis-cli ping` |
| SSL expired | `docker compose -f docker-compose.prod.yml restart certbot` |
| Full restart | `docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml --env-file .env.prod up -d` |
