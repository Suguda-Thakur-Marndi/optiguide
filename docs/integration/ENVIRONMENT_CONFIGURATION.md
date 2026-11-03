# OptiGuide — Environment & Network Configuration Guide

**Document:** `docs/integration/ENVIRONMENT_CONFIGURATION.md`  
**Status:** COMPLETE & VERIFIED  
**Date:** November 3, 2026  

---

## 1. Network Topology & Development Ports

| Component | Default Host & Port | Environment Variable Key | Default Value | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `http://localhost:8000` | `HOST`, `PORT` | `0.0.0.0`, `8000` | OpenAPI docs disabled in prod (`APP_DEBUG=false`) |
| **Vite Web App** (`apps/web`) | `http://localhost:5173` | `VITE_API_BASE_URL` | `http://localhost:8000` | Proxies `/api` to port 8000 |
| **Expo Universal Client** (`apps/mobile`) | `http://localhost:8081` | `EXPO_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Android emulator uses `http://10.0.2.2:8000` |
| **Legacy Web Alternate** | `http://localhost:3000` | N/A | N/A | Permitted by backend CORS |

---

## 2. CORS Security Architecture

The backend CORS middleware is configured in [`backend/app/main.py`](file:///c:/Users/sugud/OneDrive/Documents/optiguide/backend/app/main.py) and [`backend/app/core/config.py`](file:///c:/Users/sugud/OneDrive/Documents/optiguide/backend/app/core/config.py):

### 2.1 Permitted Origins List
```python
CORS_ORIGINS: list[str] | str = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
]
```

### 2.2 Local Development Origin Regex
In development mode (`APP_ENV != "production"`), the middleware dynamically authorizes any standard local origin:
```python
if settings.APP_ENV != "production":
    cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"
```

### 2.3 Production Security Rules
- No wildcard (`"*"`) origins are permitted when `allow_credentials=True`.
- In production (`APP_ENV=production`), exact HTTPS domain origins must be explicitly set via the `CORS_ORIGINS` environment variable.
- Private secrets (`JWT_SECRET_KEY`, `DATABASE_URL`) are strictly maintained on the backend and NEVER exposed to frontend bundles.

---

## 3. Environment Variable Templates

### 3.1 Backend Configuration (`backend/.env`)
```env
# Application Settings
APP_NAME=OptiGuide
APP_ENV=development
APP_DEBUG=true
APP_VERSION=1.0.0
API_V1_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000

# Database Connection
DATABASE_URL=sqlite:///./local_dev.db
DB_ECHO=false

# Security & Tokens
JWT_SECRET_KEY=dev-insecure-secret-key-change-in-production-optiguide-2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_GRACE_PERIOD_SECONDS=10

# Rate Limiting & Proxies
LOGIN_RATE_LIMIT_PER_MINUTE=10
REGISTER_RATE_LIMIT_PER_MINUTE=5
TRUST_FORWARDED_FOR=false
TRUSTED_PROXIES=["127.0.0.1","::1"]

# CORS Origins
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:5173","http://127.0.0.1:5173","http://localhost:8081","http://127.0.0.1:8081"]
LOG_LEVEL=INFO
```

### 3.2 Mobile / Expo Configuration (`apps/mobile/.env`)
```env
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```
*(For physical Android devices or emulators, set `EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000` or the workstation's local LAN IP).*

### 3.3 Web / Vite Configuration (`apps/web/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 4. Startup & Verification Commands

```powershell
# 1. Run Backend:
npm run backend:dev

# 2. Run React + Vite Web Client:
npm run web:dev

# 3. Run Expo Universal Client (Web Mode):
npm run frontend:web
```
