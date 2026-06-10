# 🎓 Faculty Workload Management System (FWMS)

> A full-stack web application for managing faculty teaching workload 
> allocation at Hindustan University — replacing error-prone Excel tracking.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20App-blue?style=for-the-badge)](https://fwms-workload-system.vercel.app)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=for-the-badge)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=for-the-badge)](https://neon.tech)

## 🔗 Live Demo

| | |
|---|---|
| **App** | https://fwms-workload-system.vercel.app |
| **API Docs** | https://fwms-workload-system.onrender.com/docs |
| **Demo Login** | Click **"Try Demo"** on the login page — no account needed |

> ⚠️ Backend runs on Render free tier. First load after inactivity  
> takes ~30 seconds to wake up. Please wait if the page loads slowly.

---

## ✨ Features

- 🔐 **Google OAuth** login for university staff (@hindustanuniv.ac.in)
- 👥 **Role-based access** — Admin / HOD / Coordinator / Faculty  
- 📋 **Subject preference system** — faculty submit ranked preferences (1–5)
- 📊 **Workload allocation** with teaching norm enforcement:
  - Professor: 12 hrs/week · Associate Professor: 14 hrs · Assistant: 16 hrs
- 📤 **Excel export** of finalized semester workload reports
- 🔄 **Multi-semester cycles** — Odd/Even semester switching
- 🏫 **Multi-shift, multi-section, multi-department** support

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | FastAPI (Python 3.11) + Uvicorn |
| Database | PostgreSQL on Neon (serverless) |
| Auth | Google OAuth 2.0 + JWT (HS256) |
| Containerization | Docker + Docker Compose |
| Frontend Hosting | Vercel (auto-deploy from main) |
| Backend Hosting | Render (Docker, free tier) |
| Schema Management | 39 raw SQL migrations — no ORM |

---

## 🚀 Local Development

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- PostgreSQL database (or Neon free tier)
- Google OAuth credentials

### Setup

```bash
# Clone
git clone https://github.com/Nithish-kumar-git/fwms-workload-system
cd fwms-workload-system

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, GOOGLE_CLIENT_ID etc.

# Start backend (auto-runs all 39 migrations)
docker-compose up --build
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
# App: http://localhost:5173
```

See [docs/DOCKER.md](docs/DOCKER.md) for full Docker setup.  
See [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md) for Google OAuth config.

---

## 📁 Project Structure

```
fwms-workload-system/
 ├── app/                   # FastAPI backend
 │   ├── auth/              # Google OAuth + JWT
 │   ├── core/              # Config, DB connection, middleware
 │   └── routers/           # All API route handlers
 ├── frontend/              # React + TypeScript
 │   └── src/
 │       ├── api/           # Axios API client
 │       ├── components/    # Reusable UI components
 │       └── pages/         # Page-level components
 ├── migrations/            # 39 SQL schema files (001–039)
 ├── docs/                  # Setup guides
 ├── Dockerfile             # Backend container definition
 ├── docker-compose.yml     # Local dev orchestration
 └── startup.sh             # Runs migrations then starts API
```

---

## 🔑 Environment Variables

See `.env.example` for the full list.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (keep private) |
| `GOOGLE_CLIENT_ID` | OAuth app client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth app client secret |
| `FRONTEND_URL` | Allowed CORS origin |
| `VITE_API_URL` | Backend URL for frontend build |

---

## 📄 License

MIT
