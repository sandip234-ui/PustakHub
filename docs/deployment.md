# PustakHub — Production Deployment Guide

This guide details the deployment of PustakHub to production-grade cloud environments.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Client Web Browser        |
                      +--------------+--------------+
                                     |
               HTTPS (Static SPA)    |    HTTPS / WSS (API & Events)
                                     v
                      +-----------------------------+
                      |  Frontend: Vercel (Edge CDN)|
                      |  - React 19 + Vite          |
                      |  - SPA Rewrites (vercel.json|
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Backend: Render Web Service|
                      |  - FastAPI (Python 3.11)    |
                      |  - Uvicorn ASGI Server      |
                      |  - WebSocket Endpoint (/ws) |
                      +-------+-------------+-------+
                              |             |
        SQLAlchemy + psycopg2 |             | redis-py (Pub/Sub & Cache)
                              v             v
             +------------------+         +------------------+
             | Managed Postgres |         | Managed Redis    |
             | - PostgreSQL 16+ |         | - Redis 7.x      |
             | - Alembic Schema |         | - Rate Limiter   |
             | - Row Locks      |         | - TOTP / Session |
             +------------------+         +------------------+
```

---

## 1. Frontend Deployment (Vercel)

### Prerequisites
- A GitHub repository containing the PustakHub codebase.
- A Vercel account linked to your GitHub.

### Deployment Steps
1. Navigate to the **Vercel Dashboard** and click **"Add New Project"**.
2. Import your GitHub repository.
3. In **Project Configuration**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. In **Environment Variables**, add:
   - `VITE_API_URL`: Your deployed backend API URL (e.g. `https://pustakhub-api.onrender.com/api` — no trailing slash).
5. Click **Deploy**.
6. The `frontend/vercel.json` automatically handles client-side routing rewrites so deep paths like `/catalog`, `/dashboard`, and `/users/:id` route correctly to `index.html`.

---

## 2. Backend Deployment (Render)

### Option A: Render Blueprint (Recommended)
PustakHub includes a production-ready `render.yaml` specification at the repository root.

1. In the **Render Dashboard**, click **"New"** -> **"Blueprint"**.
2. Connect your GitHub repository.
3. Render automatically discovers `render.yaml` and provisions:
   - `pustakhub-api`: FastAPI Python web service.
   - `pustakhub-db`: Managed PostgreSQL 16 database.
   - `pustakhub-redis`: Managed Redis instance.
4. Render will automatically generate secure, random values for `JWT_SECRET` and `MFA_ENCRYPTION_KEY`.
5. Under service settings, configure:
   - `CORS_ORIGINS`: Set to your deployed Vercel domain (e.g. `https://pustakhub.vercel.app`).
   - `FRONTEND_URL`: Set to your deployed Vercel URL.
   - (Optional) `SMTP_*`: Enter your production transactional email provider credentials (e.g. SendGrid, Postmark, AWS SES).
6. Click **Apply**.

### Option B: Manual Web Service Setup
1. **Create PostgreSQL Database**:
   - Name: `pustakhub-db`
   - PostgreSQL Version: 16
2. **Create Redis Instance**:
   - Name: `pustakhub-redis`
3. **Create Web Service**:
   - Runtime: Python 3
   - Root Directory: `backend`
   - Build Command: `pip install --upgrade pip && pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/api/health`

---

## 3. Production Environment Variables Reference

| Variable | Description | Example / Setting |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Application mode | `production` |
| `DEBUG` | FastAPI debug mode | `false` |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URI | `postgresql+psycopg2://user:pass@host/db` |
| `REDIS_URL` | Redis connection URI | `redis://user:pass@host:port/0` |
| `JWT_SECRET` | 256-bit cryptographic signing secret | `openssl rand -hex 32` |
| `JWT_ALGORITHM` | Algorithm for token signatures | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifespan | `7` |
| `MFA_ENCRYPTION_KEY` | 32-byte key for AES-256-GCM encryption | `openssl rand -hex 32` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `https://pustakhub.vercel.app` |
| `FRONTEND_URL` | Canonical frontend domain for email links | `https://pustakhub.vercel.app` |
| `RATE_LIMIT_ENABLED` | Enables Redis sliding-window limiter | `true` |
| `ENABLE_SECURITY_HEADERS` | Injects CSP, X-Frame-Options, etc. | `true` |
| `ENABLE_HSTS` | Injects Strict-Transport-Security | `true` |

---

## 4. Alternative: Docker & Container Orchestration

To run the entire stack locally or on a VPS (AWS EC2, DigitalOcean Droplet, Hetzner):

```bash
# Clone the repository
git clone https://github.com/<YOUR-USERNAME>/PustakHub.git
cd PustakHub

# Launch PostgreSQL, Redis, FastAPI Backend, and React Frontend
docker compose up --build -d

# Verify services
docker compose ps
curl http://localhost:8000/api/health
```

---

## 5. Post-Deployment Verification Checklist

1. [ ] **Health Endpoint**: `GET https://<api-domain>/api/health` returns `{"status": "healthy", "database": "connected", "redis": "connected"}`.
2. [ ] **Database Schema**: Verify Alembic migration is at head `3741532892a9`.
3. [ ] **CORS Verification**: Ensure cross-origin requests from the Vercel frontend succeed without browser CORS blocks.
4. [ ] **Authentication**: Register a new user, verify OTP, log in, and verify JWT token issuance.
5. [ ] **WebSocket Realtime**: Inspect browser network panel on `/catalog` to confirm active WSS connection to `/api/v1/realtime/ws`.
6. [ ] **No Secret Exposure**: Verify logs contain no plaintext passwords, tokens, OTPs, or database credentials.
