# OptiGuide — Phase 2 Report
## Authentication, Authorization & User Management

**Project:** OptiGuide Preliminary Vision Screening and Eyewear Guidance  
**Phase:** Phase 2  
**Date:** November 3, 2026  
**Status:** COMPLETE (All Acceptance Criteria Verified)  
**Report Path:** `docs/phase-reports/PHASE_2_REPORT.md`  

---

## 1. Phase Overview

### 1.1 Objective and Scope
Phase 2 implemented a production-grade, secure, and maintainable authentication and authorization system for **OptiGuide**, extending the successfully completed Phase 1 backend foundation.

The scope encompassed:
- User registration and login flows.
- OWASP-recommended Argon2id password hashing.
- Short-lived JWT access tokens (15 minutes) and persistent refresh token rotation (7 days).
- Refresh token reuse detection with immediate revocation of all compromised user sessions.
- Session management (single-session logout, all-sessions logout, session listing).
- Role-Based Access Control (RBAC) supporting `patient`, `optometrist`, `shopkeeper`, and `admin`.
- User profile management (`GET /api/v1/users/me`, `PATCH /api/v1/users/me`).
- Administrative account activation and deactivation (`PATCH /api/v1/users/{id}/status`).
- In-memory sliding-window rate limiting for registration and login endpoints.
- Database persistence with forward-only Alembic migration `002_user_and_auth.py`.
- Automated test suites (unit, API, and integration).

### 1.2 Completed Features
- [x] Declarative SQLAlchemy models: `User` and `UserSession`.
- [x] Argon2id password hashing via `argon2-cffi`.
- [x] JWT access tokens via `pyjwt` with claim verification (`sub`, `iss`, `aud`, `exp`, `type="access"`).
- [x] Persistent refresh token sessions stored as SHA-256 hashes (`user_sessions` table).
- [x] Token rotation on `/refresh` and automatic session-wide revocation upon reuse detection.
- [x] Single session logout (`POST /api/v1/auth/logout`) and multi-session logout (`POST /api/v1/auth/logout-all`).
- [x] Authenticated user identity endpoints (`GET /api/v1/auth/me` and `GET /api/v1/users/me`).
- [x] Profile updates (`PATCH /api/v1/users/me`).
- [x] User session inspection (`GET /api/v1/users/me/sessions`).
- [x] Administrator account management (`PATCH /api/v1/users/{id}/status`).
- [x] RBAC permission dependencies: `get_current_user`, `get_current_active_user`, `require_roles`, `require_admin`.
- [x] Sliding-window rate limiting dependency (5/min for register, 10/min for login).
- [x] Alembic migration `002_user_and_auth.py` with verified upgrade and downgrade cycles.
- [x] 65 passing automated tests (100% pass rate).
- [x] 100% Ruff lint and format compliance.

### 1.3 Incomplete or Deferred Features (Phase 3 Scope)
- Vision screening domain models (`ScreeningSession`, `VisualAcuityRecord`, `TumblingEResult`).
- Computer vision distance calibration and image processing pipelines.
- Eyewear frame catalog models (`Frame`, `Brand`, `LensType`).
- Eyewear recommendation engine.
- Prescription validation and PDF clinical export services.

---

## 2. Repository Changes

### 2.1 File Inventory
| Action | Relative Path | Purpose |
|---|---|---|
| **Created** | `backend/app/models/user.py` | Declarative SQLAlchemy User entity |
| **Created** | `backend/app/models/session.py` | Declarative SQLAlchemy UserSession entity |
| **Created** | `backend/app/core/security.py` | Argon2id password hashing and JWT access token engine |
| **Created** | `backend/app/schemas/auth.py` | Pydantic v2 schemas for auth, registration, tokens, and sessions |
| **Created** | `backend/app/repositories/user_repo.py` | Data access repository for User entities |
| **Created** | `backend/app/repositories/session_repo.py` | Data access repository for UserSession entities |
| **Created** | `backend/app/services/auth_service.py` | Domain service for registration, authentication, rotation, logout |
| **Created** | `backend/app/services/user_service.py` | Domain service for profile management and session listing |
| **Created** | `backend/app/api/v1/auth.py` | `/api/v1/auth/` endpoints router |
| **Created** | `backend/app/api/v1/users.py` | `/api/v1/users/` endpoints router |
| **Created** | `backend/migrations/versions/002_user_and_auth.py` | Alembic migration for users and user_sessions tables |
| **Created** | `backend/tests/unit/test_security_auth.py` | Unit tests for Argon2id hashing, JWT claims, and rate limiting |
| **Created** | `backend/tests/api/test_auth_api.py` | API tests for auth endpoints |
| **Created** | `backend/tests/api/test_users_api.py` | API tests for user profile and admin endpoints |
| **Created** | `backend/tests/integration/test_auth_integration.py` | Integration tests for session persistence and token rotation |
| **Created** | `docs/backend/PHASE_2_PRE_IMPLEMENTATION_AUDIT.md` | Pre-implementation audit artifact |
| **Created** | `docs/backend/PHASE_2_AUTHENTICATION_DESIGN.md` | Architecture design specification |
| **Created** | `docs/backend/PHASE_2_SECURITY_AUDIT.md` | Comprehensive security review |
| **Created** | `docs/backend/PHASE_2_COMPLETION_REPORT.md` | Phase 2 completion artifact |
| **Created** | `docs/phase-reports/PHASE_2_REPORT.md` | This phase report |
| **Modified** | `backend/pyproject.toml` | Added `argon2-cffi`, `pyjwt`, `email-validator` dependencies |
| **Modified** | `backend/requirements.txt` | Pinned auth dependencies |
| **Modified** | `backend/README.md` | Documented auth endpoints, architecture, and security settings |
| **Modified** | `backend/.env.example` | Added JWT, password, and rate-limiting configuration template |
| **Modified** | `backend/app/core/config.py` | Added JWT settings with production secret validation |
| **Modified** | `backend/app/core/exceptions.py` | Added custom auth and authorization exception hierarchy |
| **Modified** | `backend/app/middleware/error_handler.py` | Added `optiguide_exception_handler` mapping to RFC envelopes |
| **Modified** | `backend/app/main.py` | Registered `OptiGuideException` handler and auth/users routers |
| **Modified** | `backend/app/models/__init__.py` | Registered `User` and `UserSession` declarative models |
| **Modified** | `backend/app/api/dependencies.py` | Added `get_current_user`, `get_current_active_user`, `require_roles`, `rate_limit` |
| **Modified** | `backend/app/api/v1/router.py` | Mounted `/auth` and `/users` routers |
| **Modified** | `backend/tests/conftest.py` | Added automatic rate limiter state cleanup between tests |

---

## 3. Implementation Details

### 3.1 Key Classes, Endpoints, and Dependencies

#### 1. Security Engine (`backend/app/core/security.py`)
- `hash_password(password: str) -> str`: Uses `argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=argon2.Type.ID)`.
- `verify_password(plain: str, hashed: str) -> bool`: Verifies plaintext against Argon2id hash.
- `create_access_token(user_id, email, role) -> tuple[str, int]`: Encodes JWT access token with 15-minute expiration, `iss="optiguide-api"`, `aud="optiguide-client"`, `type="access"`.
- `decode_access_token(token: str) -> dict`: Decodes and validates JWT claims, raising `TokenExpiredException` or `TokenInvalidException`.
- `hash_token(raw_token: str) -> str`: Produces SHA-256 hex digest for refresh token database storage.

#### 2. Models (`backend/app/models/`)
- `User`: Primary key `id` (UUID), `email` (unique index), `hashed_password`, `full_name`, `role`, `phone_number`, `preferred_language`, `is_active`, `is_verified`, timestamps.
- `UserSession`: Primary key `id` (UUID), `user_id` (foreign key to `users.id` with cascade delete), `session_token_hash` (unique index), `user_agent`, `ip_address`, `is_revoked`, `expires_at`, `created_at`, `revoked_at`.

#### 3. FastAPI Dependencies (`backend/app/api/dependencies.py`)
- `get_current_user`: Resolves and validates JWT from `Authorization: Bearer <token>`, fetches user entity from database, verifies `is_active`.
- `get_current_active_user`: Enforces `user.is_active is True`.
- `require_roles(*roles)`: Enforces user role membership (`patient`, `optometrist`, `shopkeeper`, `admin`), raising HTTP 403 Forbidden with standard envelope if unauthorized.
- `rate_limit(max_requests, window_seconds)`: In-memory sliding-window request tracker returning HTTP 429 when threshold exceeded.

#### 4. API Endpoints (`backend/app/api/v1/`)
- `POST /api/v1/auth/register`: 201 Created, returns `AuthResponse`.
- `POST /api/v1/auth/login`: 200 OK, returns `AuthResponse`.
- `POST /api/v1/auth/refresh`: 200 OK, rotates token and returns `TokenRefreshResponse`.
- `POST /api/v1/auth/logout`: 200 OK, marks session revoked.
- `POST /api/v1/auth/logout-all`: 200 OK, revokes all sessions for user.
- `GET /api/v1/auth/me`: 200 OK, returns `UserProfileResponse`.
- `GET /api/v1/users/me`: 200 OK, returns `UserProfileResponse`.
- `PATCH /api/v1/users/me`: 200 OK, updates profile fields.
- `GET /api/v1/users/me/sessions`: 200 OK, returns active/revoked sessions.
- `PATCH /api/v1/users/{id}/status`: 200 OK, admin activates/deactivates accounts.

---

## 4. Testing and Verification

### 4.1 Environment & Software Versions
- **Host OS:** Windows 11 (build 26100, x86_64)
- **Shell:** Windows PowerShell 5.1
- **Python Version:** 3.13.14
- **Pytest:** 8.4.2
- **Ruff:** 0.17.3
- **SQLAlchemy:** 2.1.6
- **FastAPI:** 0.162.0
- **Alembic:** 1.20.1
- **Argon2-cffi:** 25.1.0
- **PyJWT:** 2.15.1

### 4.2 Executed Automated Tests
All 65 tests executed synchronously via PowerShell and passed with zero failures:
- **36 Phase 1 Tests:** Health checks, configuration validation, exception serialization, database session lifecycle, database test isolation.
- **29 Phase 2 Tests:** Argon2id password hashing, JWT decoding, token expiration, token tampering, rate-limiting, registration, duplicate rejection, weak password rejection, login, invalid login rejection, refresh token rotation, refresh token reuse detection, single logout, logout all, profile retrieval, profile updates, session listing, admin role enforcement, user deactivation.

```powershell
Command: & "backend/.venv/Scripts/python" -m pytest backend/tests -v
Result:  65 passed in 1.58s (100% pass rate)
```

```powershell
Command: & "backend/.venv/Scripts/ruff" check backend
Result:  All checks passed!
```

```powershell
Command: & "backend/.venv/Scripts/ruff" format --check backend
Result:  52 files already formatted
```

---

## 5. Known Issues & Technical Debt

1. **In-Memory Rate Limiting:**
   The sliding-window rate limiter is currently in-memory. For single-process instances this provides robust protection; for horizontal scaling across multiple container replicas or Uvicorn workers in production, a shared Redis instance should back the rate limiter in future phases.
2. **Upstream Starlette Deprecation Warnings:**
   Non-blocking Starlette 0.45 warnings (`httpx` in `starlette.testclient`, `HTTP_422_UNPROCESSABLE_ENTITY`).

---

## 6. Next Phase Handoff (Phase 3 Readiness)

### 6.1 Completed Prerequisites
- [x] User entity and authentication subsystem operational.
- [x] JWT access tokens and persistent refresh token rotation active.
- [x] RBAC enforcement active (`patient`, `optometrist`, `shopkeeper`, `admin`).
- [x] Alembic migration `002_user_and_auth.py` applied and verified.
- [x] 65 passing tests with zero regressions.

### 6.2 Recommended Next Steps for Phase 3
1. **Vision Screening Data Models:**
   Create models for `ScreeningSession`, `VisualAcuityRecord`, and `SnellenTestResult` linked to `users.id` via foreign key.
2. **Interactive Screening Pipelines:**
   Develop mobile UI components for tumbling E / Snellen chart testing with automated distance calibration.
3. **Eyewear Recommendation Catalog:**
   Create catalog schemas for frames, lens types, and coatings; implement recommendation engine matching facial dimensions and acuity results.

---

## 7. Sign-Off & Verification

| Role | Status | Notes |
|---|---|---|
| **Principal Backend Architect** | **APPROVED** | Modular architecture, layer separation, repository pattern verified |
| **Application Security Engineer** | **APPROVED** | Argon2id, JWT validation, token reuse detection, rate limiting verified |
| **Database Architect** | **APPROVED** | Alembic migration 002 applied, upgrade and downgrade cycles verified |
| **QA Automation Engineer** | **APPROVED** | 65/65 tests passed, 100% Ruff compliance, dual-startup verified |
