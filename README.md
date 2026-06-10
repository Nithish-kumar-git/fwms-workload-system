# 🎓 Faculty Workload Management System (FWMS)

> A full-stack web app for managing faculty teaching workload allocation
> at Hindustan University — replacing manual Excel-based tracking.

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

> ⚠️ Backend on Render free tier — first load after inactivity takes ~30s.
> The login page will show a "waking up" notice automatically.

---

## ✨ Features

- 🔐 **Google OAuth** login for university staff (@hindustanuniv.ac.in)
- 👥 **Role-based access** — Admin / HOD / Coordinator / Faculty
- 📋 **Subject preference system** — faculty rank preferences (1–5)
- 📊 **Workload allocation** with teaching norm enforcement:
  Professor 12h · Associate Professor 14h · Assistant Professor 16h
- 📤 **Excel export** of finalized semester workload reports
- 🔄 **Multi-semester cycle** management (Odd / Even switching)
- 🏫 **Multi-shift, multi-section, multi-department** support
- ⏳ **Cold start detection** — login page auto-detects backend wake-up

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

```bash
# Clone
git clone https://github.com/Nithish-kumar-git/fwms-workload-system
cd fwms-workload-system

# Backend
cp .env.example .env    # fill in DATABASE_URL, SECRET_KEY, etc.
docker-compose up --build
# API at http://localhost:8000 | Docs at http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# App at http://localhost:5173
```

See [docs/DOCKER.md](docs/DOCKER.md) and [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md).

---

## 📁 Project Structure

```
fwms-workload-system/
 ├── app/                   # FastAPI backend
 │   ├── auth/              # Google OAuth + JWT
 │   ├── core/              # Config, DB, middleware
 │   └── routers/           # API route handlers
 ├── frontend/src/          # React + TypeScript
 │   ├── api/               # Axios API client
 │   ├── components/        # Reusable UI components
 │   └── pages/             # Page components
 ├── migrations/            # 39 SQL schema files (001–039)
 ├── docs/                  # Setup guides
 ├── Dockerfile
 ├── docker-compose.yml
 └── startup.sh             # Runs migrations then starts API
```

---

## 🔑 Key Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `FRONTEND_URL` | Allowed CORS origin |
| `VITE_API_URL` | Backend URL (set in Vercel dashboard) |

Full list in `.env.example`.

---

## 📄 License

MIT
