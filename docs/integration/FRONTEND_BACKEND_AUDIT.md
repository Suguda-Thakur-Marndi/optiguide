# OptiGuide — Frontend & Backend Integration Audit

**Document:** `docs/integration/FRONTEND_BACKEND_AUDIT.md`  
**Status:** COMPLETE  
**Audience:** Technical Lead, Senior Full-Stack Engineers, Security Engineers  
**Date:** November 3, 2026  

---

## 1. Executive Summary

This repository audit inspects the existing OptiGuide frontend and FastAPI backend implementations to establish the baseline for full end-to-end integration without disrupting or redesigning any teammate-authored code.

---

## 2. Actual Frontend Framework & Structure

The repository contains a monorepo architecture with two complementary frontend applications sharing common contracts:

### 2.1 Universal Client (`apps/mobile`)
- **Framework:** React Native `0.76.6`
- **Platform Tooling:** Expo SDK `~52.0.0`
- **Web Runtime:** `react-native-web` `~0.19.13`
- **Routing Engine:** Expo Router file-based routing (`apps/mobile/app/`)
- **Language:** TypeScript `^5.3.3` (Strict mode)
- **Component Architecture:** Atomic reusable UI primitives in `src/components/` (`Button`, `TextField`, `ScreenContainer`, `LoadingIndicator`, `ErrorMessage`), screen views in `src/screens/` and domain features in `src/features/screening/`.
- **Design Tokens:** `src/theme/tokens.ts` (colors, spacing, typography, borderRadius, elevation).
- **Environment Variable Convention:** `EXPO_PUBLIC_API_BASE_URL` (reads via `process.env` and `expo-constants`).
- **Testing Framework:** Jest `^29.7.0` with `jest-expo` `~52.0.0`.

### 2.2 Dedicated Web Client (`apps/web`)
- **Framework:** React `18.3.1`
- **Build Tool:** Vite `5.4.10`
- **Language:** TypeScript `^5.3.3`
- **Environment Variable Convention:** `VITE_API_BASE_URL` and `vite.config.ts` reverse proxy (`/api` -> `http://localhost:8000`).
- **Testing Framework:** Node.js native test runner (`node --test tests/*.test.js`).

### 2.3 Shared Contract Package (`shared`)
- **Namespace:** `@optiguide/shared`
- **Location:** `shared/`
- **Exports:** Typed contracts for API responses, User Profiles, Auth tokens, Screening Sessions, Consent status, and clinical constants.

---

## 3. Actual Backend Framework & Structure

- **Framework:** FastAPI `0.115.11`
- **Runtime:** Python `3.13.14` (declaring `>=3.12` compatibility)
- **ORM & Database:** SQLAlchemy `2.0.38` with SQLite (`local_dev.db`) for development/tests, and `psycopg` binary `3.2.0` for PostgreSQL.
- **Migrations:** Alembic `1.15.1` (migrations `001_initial_baseline`, `002_user_and_auth`, `003_screening_consent_and_session`).
- **Security & Authentication:** Argon2id (`argon2-cffi`), JWT HS256 (`pyjwt`), sliding-window in-memory rate limiting with anti-spoofing client IP resolution.
- **Testing:** Pytest `8.4.2` with `pytest-asyncio` and `httpx`.

---

## 4. Existing API Endpoints Inventory

### 4.1 System & Health (`/api/v1/health`)
- `GET /` — Root application identification metadata
- `GET /health` — Service liveness probe
- `GET /api/v1/health` — Composite health probe (API + DB status)
- `GET /api/v1/health/db` — Dedicated database latency diagnostic

### 4.2 Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Patient registration (returns JWT access + refresh token)
- `POST /api/v1/auth/login` — Password authentication (anti-enumeration protected)
- `POST /api/v1/auth/refresh` — Atomic refresh token rotation
- `POST /api/v1/auth/logout` — Single-session revocation
- `POST /api/v1/auth/logout-all` — Revoke all active sessions for authenticated user
- `GET /api/v1/auth/me` — Authenticated user identity inspection

### 4.3 User Management (`/api/v1/users`)
- `GET /api/v1/users/me` — User profile details
- `PATCH /api/v1/users/me` — Self-profile update (`full_name`, `phone_number`, `preferred_language`)
- `GET /api/v1/users/me/sessions` — Active and historical login sessions
- `PATCH /api/v1/users/{user_id}/status` — Administrator role & activation control
- `GET /api/v1/users/clinical/review-access` — Verified eye-care professional access check

### 4.4 Screening Consent & Sessions (`/api/v1/screening`)
- `GET /api/v1/screening/consent/current` — Canonical consent document (v1.0.0) + SHA-256 hash
- `POST /api/v1/screening/consent/accept` — Idempotent cryptographic consent agreement
- `POST /api/v1/screening/consent/withdraw` — Consent revocation with active session cascade cancellation
- `POST /api/v1/screening/sessions` — Initialize screening session (single-active concurrency constraint)
- `GET /api/v1/screening/sessions` — Paginated user session list
- `GET /api/v1/screening/sessions/{id}` — Session detail retrieval (IDOR protected: 404 on unowned)
- `POST /api/v1/screening/sessions/{id}/complete` — Mark in-progress session completed
- `POST /api/v1/screening/sessions/{id}/cancel` — Cancel in-progress session with structured reason

---

## 5. Existing Frontend Routes & Status

| Route | Platform | Description | Integration Status |
| :--- | :--- | :--- | :--- |
| `apps/mobile/app/(tabs)/index.tsx` | Mobile / Web | Main Dashboard | Integrated with `HomeScreen.tsx` |
| `apps/mobile/app/(tabs)/diagnostics.tsx` | Mobile / Web | Health & DB Telemetry | Fully Connected to `/api/v1/health` |
| `apps/mobile/app/(auth)/login.tsx` | Mobile / Web | Authentication Screen | **Stub requires connection** |
| `apps/mobile/app/profile/index.tsx` | Mobile / Web | User Profile & Sessions | **Stub requires connection** |
| `apps/mobile/app/screening/index.tsx` | Mobile / Web | Full Screening Flow | Fully Connected to `/api/v1/screening/*` |
| `apps/web/src/App.tsx` | Web (Vite) | Full Web Application | Fully Connected to all API endpoints |

---

## 6. Gaps & Missing Integration Components

1. **`apps/mobile` Auth & User Endpoints Missing from API Client:**  
   `apps/mobile/src/services/apiClient.ts` contained health and screening endpoints, but lacked `register()`, `login()`, `refresh()`, `logout()`, `logoutAll()`, `getCurrentUser()`, `updateProfile()`, and `getUserSessions()`.
2. **Mobile Screen Stubs:**  
   `apps/mobile/app/(auth)/login.tsx` and `apps/mobile/app/profile/index.tsx` were placeholder screens with static text, needing connection to the live authentication and profile management APIs.
3. **Automatic 401 Interception & Refresh:**  
   Neither mobile nor web API clients had automatic token refresh queueing to catch expired access tokens (15-minute expiry) and refresh them silently before retrying requests.

---

## 7. Security & Privacy Audit Findings

1. **Token Transport:**  
   Tokens are returned via RFC 6749 JSON responses. Refresh tokens must never be logged. On Web, tokens are cached in `localStorage`; on native devices, secure platform storage is recommended for production.
2. **Strict RBAC & Privilege Escalation:**  
   The backend strictly blocks self-registration of `admin` or `optometrist` roles. The frontend forms must never allow selecting privileged roles during public signup.
3. **Anti-Enumeration Timing Safety:**  
   The backend uses dummy Argon2id hash computations to prevent user existence enumeration. Frontend error messaging must remain uniformly generic ("Invalid email or password").
4. **Clinical Boundary:**  
   The application strictly provides preliminary vision screening and does NOT diagnose conditions or calculate lens prescriptions. Disclaimers are enforced before screening sessions can start.

---

## 8. Integration Implementation Plan

1. **Extend Mobile API Client (`apps/mobile/src/services/apiClient.ts`):**  
   Add full authentication (`register`, `login`, `refresh`, `logout`, `logoutAll`), user profile (`getMe`, `updateProfile`, `getUserSessions`), and automatic 401 retry handling.
2. **Extend Web API Client (`apps/web/src/services/apiClient.ts`):**  
   Add `logoutAll()`, `updateProfile()`, and `getUserSessions()`.
3. **Connect Mobile Auth Screen (`apps/mobile/app/(auth)/login.tsx`):**  
   Provide clean login/register forms using existing `TextField`, `Button`, and `ErrorMessage` components.
4. **Connect Mobile Profile Screen (`apps/mobile/app/profile/index.tsx`):**  
   Display profile details, editable fields (name, phone), session history, and logout controls.
5. **Eliminate All Production Mock Data:**  
   Ensure all active screens fetch real data and present appropriate empty states when records are absent.
6. **Execute Complete Test Suites & Manual End-to-End Verification.**
