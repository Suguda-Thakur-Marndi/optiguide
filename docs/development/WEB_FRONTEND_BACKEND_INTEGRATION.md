# OptiGuide — Web Frontend & Backend Integration Guide

**Document:** `docs/development/WEB_FRONTEND_BACKEND_INTEGRATION.md`  
**Status:** COMPLETE & VERIFIED  
**Platforms:** Web (React + Vite & Expo React Native Web) + FastAPI Backend  

---

## 1. Overview & Architecture

OptiGuide supports two frontend web experiences, both fully integrated with the FastAPI backend:

```
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│       apps/web (React + Vite)        │     │  apps/mobile (Expo React Native Web) │
│        http://localhost:5173         │     │         http://localhost:8081        │
└──────────────────┬───────────────────┘     └──────────────────┬───────────────────┘
                   │                                            │
                   │ (HTTP REST / JSON with Bearer Auth)        │
                   │                                            │
                   ▼                                            ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend (Port 8000)                             │
│   • CORS enabled for: 5173, 4173, 8081, 19006, 3000, 8080 (localhost & 127.0.0.1)│
│   • Health (/api/v1/health, /api/v1/health/db)                                    │
│   • Auth & Users (/api/v1/auth/*, /api/v1/users/*)                                │
│   • Consent & Screening (/api/v1/screening/*)                                     │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                         PostgreSQL / SQLite Database
```

---

## 2. Quick Start: Running Frontend & Backend

### 2.1 Starting the FastAPI Backend
Open a terminal in the repository root:
```powershell
# Using npm script:
npm run backend:dev

# Or using dedicated PowerShell script:
powershell -ExecutionPolicy Bypass -File scripts/run_backend.ps1

# Direct virtual environment command:
backend/.venv/Scripts/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
The backend starts at `http://localhost:8000`.

### 2.2 Starting the React + Vite Web App (`apps/web`)
Open a second terminal in the repository root:
```powershell
npm run web:dev
```
Open your browser to:
👉 **`http://localhost:5173`**

### 2.3 Starting the Universal Expo Web App (`apps/mobile`)
Alternatively, to run the universal Expo client in web mode:
```powershell
npm run frontend:web
```
Open your browser to:
👉 **`http://localhost:8081`**

---

## 3. Connected Features in the Web App

The Web App (`apps/web/src/App.tsx`) connects to all backend services:

### 1. System Health & Database Diagnostics (`/api/v1/health`, `/api/v1/health/db`)
- Live connection indicator: **Backend Live** (green), **Connecting** (yellow), **Backend Offline** (red).
- Base URL input to easily switch between localhost, 127.0.0.1, or staging APIs.
- Real-time database status, database dialect (SQLite/PostgreSQL), and ping latency (ms).

### 2. User Authentication & Profile (`/api/v1/auth/*`, `/api/v1/users/*`)
- **Register:** Create patient accounts (`POST /api/v1/auth/register`).
- **Sign In:** Authenticate with password validation (`POST /api/v1/auth/login`).
- **Token Management:** Access and refresh tokens stored safely in `localStorage`.
- **Profile Card:** User ID, role badge, verification state, creation timestamp.
- **Clinical Review Access Check:** Test professional authorization boundary (`GET /api/v1/users/clinical/review-access`).
- **Sign Out:** Invalidate session (`POST /api/v1/auth/logout`) and clear tokens.

### 3. Screening Consent Lifecycle (`/api/v1/screening/consent/*`)
- View server-controlled consent document version (`1.0.0`).
- Verify SHA-256 integrity hash (`ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6`).
- Review the mandatory clinical disclaimer.
- Accept consent (`POST /api/v1/screening/consent/accept`).
- Withdraw consent (`POST /api/v1/screening/consent/withdraw`), triggering automatic active session cancellation.

### 4. Vision Screening Sessions (`/api/v1/screening/sessions/*`)
- **Start Session:** Initializes new `IN_PROGRESS` session with browser device metadata and notes.
- **Single-Active-Session Guard:** Handles 409 Conflict gracefully if a session is already active.
- **Active Session Tracker:** Displays session ID, elapsed timer, and action buttons.
- **Complete Session:** Marks active screening session as completed (`POST /api/v1/screening/sessions/{id}/complete`).
- **Cancel Session:** Select structured reason (`user_cancelled`, `interrupted`, `technical_issue`) and cancel (`POST /api/v1/screening/sessions/{id}/cancel`).
- **Session History Table:** Displays past sessions with colored status badges (`COMPLETED`, `CANCELLED`, `IN_PROGRESS`).

---

## 4. CORS & Network Configuration

The backend CORS settings (`backend/app/core/config.py`) explicitly permit:
- `http://localhost:5173` & `http://127.0.0.1:5173` (Vite dev)
- `http://localhost:4173` & `http://127.0.0.1:4173` (Vite preview)
- `http://localhost:8081` & `http://127.0.0.1:8081` (Expo web)
- `http://localhost:3000` & `http://127.0.0.1:3000` (Standard web)
- `http://localhost:8080` & `http://127.0.0.1:8080` (Alternative web)
- `http://localhost:19006` & `http://127.0.0.1:19006` (Legacy Expo web)

Additionally, `apps/web/vite.config.ts` includes a dev proxy routing `/api` requests directly to `http://localhost:8000`.

---

## 5. Verification Commands

To verify all test suites across backend, mobile web, and React web:

```powershell
# 1. Backend tests (112 tests including CORS verification)
backend/.venv/Scripts/python -m pytest backend/tests -v

# 2. Web app build & tests
npm run web:build
npm run web:test

# 3. Mobile web build & tests
npm run frontend:build:web
npm run frontend:test
```
