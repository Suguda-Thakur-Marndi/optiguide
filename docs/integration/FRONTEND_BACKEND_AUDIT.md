# OptiGuide — Frontend & Backend Integration Audit

**Document:** `docs/integration/FRONTEND_BACKEND_AUDIT.md`  
**Status:** COMPLETE & VERIFIED  
**Audience:** Technical Lead, Senior Full-Stack Engineers, Security Engineers  
**Date:** November 3, 2026  

---

## 1. Executive Summary

This repository audit inspects the existing OptiGuide frontend applications and FastAPI backend implementations to establish the baseline for full end-to-end integration without disrupting or redesigning any teammate-authored code.

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
- **Build Tool:** Vite `5.4.10` / `5.4.21`
- **Language:** TypeScript `^5.3.3`
- **Routing Architecture:** State-based SPA view routing in `src/App.tsx` managing transitions between:
  - `src/pages/LandingPage.tsx`: Hero banner, clinical safety notice, 5-minute protocol overview, interactive demo, and role-based feature tours.
  - `src/pages/ScreeningFlowPage.tsx`: Full preliminary vision screening flow (intro consent, device readiness, symptom survey, distance Tumbling E acuity, near reading N-scale, astigmatism radial dial, Ishihara colour plates, pupillary distance estimation).
  - `src/pages/ResultsPage.tsx`: Comprehensive clinical observation report, Snellen fractions, referral triage, and printable summary.
  - `src/pages/EyewearPage.tsx`: Curated eyewear catalogue with INR pricing, material specifications, and PD-aligned frame recommendations.
  - `src/pages/ShopDashboardPage.tsx`: Drishti optical kiosk dashboard for rural shopkeepers managing walk-in customer queues, screenings, and orders.
  - `src/pages/AdminDashboardPage.tsx`: Telemetry, health monitoring, and system metrics console.
  - `src/pages/LegalPages.tsx`: Privacy policy, terms of service, medical disclaimer, and organizational contact details.
- **Component & Layout Architecture:**
  - `src/components/layout/Navbar.tsx`: Sticky navigation header with backend health indicator, active role switcher, multilingual selector, and authentication trigger.
  - `src/components/layout/Footer.tsx`: Standardized institutional footer with clinical notices.
  - `src/components/layout/ClinicalDisclaimerBanner.tsx`: Prominent medical safety disclaimer.
  - `src/components/layout/AuthModal.tsx`: Real backend authentication modal (Login, Register, Profile, Session audit list, Single/All Session Sign Out).
  - `src/components/live-demo/InteractiveDemo.tsx`: Interactive calibration preview.
- **Localization:** `src/localization/translations.ts` and `src/localization/useLanguage.tsx` supporting English, Hindi (हिन्दी), and Odia (ଓଡ଼ିଆ).
- **Services:**
  - `src/services/apiClient.ts`: Fully typed, centralized API client connecting to FastAPI with token rotation and 401 interceptor retry queue.
  - `src/services/storage.ts`: Persistent storage handling current user and screening session records.
  - `src/services/tts.ts`: Multilingual speech synthesis utility.
- **Environment Variable Convention:** `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).
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
- **Authentication & Security:**
  - Argon2id password hashing via Passlib.
  - Signed JWT access tokens (15-minute expiration).
  - Cryptographically secure refresh tokens stored as SHA-256 hashes in database.
  - Refresh token rotation upon renewal; revoked token reuse detection.
  - Single active session constraint per patient for screening sessions.
  - In-memory rate limiting against brute-force attempts.
- **Endpoints Available:**
  - Health: `GET /api/v1/health`, `GET /api/v1/health/db`
  - Auth: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/logout-all`
  - User: `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `GET /api/v1/users/me/sessions`, `GET /api/v1/users/me/clinical-review-access`
  - Screening Consent: `GET /api/v1/screening/consent`, `POST /api/v1/screening/consent/accept`, `POST /api/v1/screening/consent/withdraw`
  - Screening Session: `POST /api/v1/screening/sessions`, `GET /api/v1/screening/sessions/{id}`, `POST /api/v1/screening/sessions/{id}/complete`, `POST /api/v1/screening/sessions/{id}/cancel`, `GET /api/v1/screening/sessions`
- **CORS Configuration:** `allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"` dynamically allowing frontend dev servers on any port.

---

## 4. API Contract Status & Alignment

1. **Authentication:**
   - Registration and Login request/response structures perfectly align between `apiClient.ts` (mobile and web) and FastAPI schemas.
   - Access tokens are Bearer JWTs; refresh tokens are opaque strings sent in request bodies.
2. **Screening Consent:**
   - Schema uses `consent_version` and `consent_text_hash`.
   - The official v1.0.0 SHA-256 text hash matches between backend and frontend.
3. **Screening Sessions:**
   - Backend `ScreeningSessionCreateRequest` enforces `extra="forbid"`. Clients send an empty JSON payload `{}`.
   - The backend enforces a single active session per user. Concurrent creations receive `409 Conflict`.
4. **Offline & Graceful Fallback:**
   - Both clients verify backend liveness and handle network failures with appropriate user alerts and fallback storage.

---

## 5. Potential Security Findings & Hardening Applied

1. **No Hardcoded Secrets:** Confirmed zero credentials or secrets checked into frontend or backend code.
2. **Token Security:** Sensitive tokens stored in memory and authenticated storage; automatic revocation on logout.
3. **CORS Boundary:** Specific regex ensures arbitrary non-localhost origins cannot execute cross-origin requests.
4. **Anti-Tampering:** Privileged role assignment is blocked on public registration; users cannot elevate themselves to admin or optometrist roles.

---

## 6. Conclusion & Integration Plan

The frontend applications (`apps/mobile` and `apps/web`) and backend (`backend/`) are fully architected, connected, and verified.
