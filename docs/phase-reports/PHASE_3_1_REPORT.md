# OptiGuide — Phase 3.1 Completion Report
## Consent Management & Screening Session Foundation

**Project:** OptiGuide Preliminary Vision Screening and Eyewear Guidance  
**Lead Roles:** Principal Software Architect, Senior FastAPI Backend Engineer, React Native Architect, Database Architect, Application Security Engineer, QA Automation Lead  
**Date:** November 3, 2026  
**Status:** COMPLETE (All Acceptance Criteria Verified)  
**Report Path:** `docs/phase-reports/PHASE_3_1_REPORT.md`  

---

## 1. Phase Overview

Phase 3.1 established a production-grade, cryptographically validated consent management and screening session lifecycle foundation for OptiGuide. It bridges the FastAPI backend, Alembic migrations, PostgreSQL/SQLite databases, shared TypeScript contracts, and the React Native / Expo cross-platform mobile and web frontend.

### 1.1 Phase Objective and Scope
- Establish a legally defensible and privacy-conscious screening consent system.
- Build a robust screening session lifecycle (`IN_PROGRESS` $\to$ `COMPLETED` / `CANCELLED`) with strict state machine validation.
- Implement concurrency safeguards allowing only one active screening session per patient at a time.
- Enforce full non-diagnostic medical boundaries (strictly rejecting prescription parameters or clinical diagnostic terminology).
- Create a complete, accessible, cross-platform frontend experience in React Native / Expo.
- Ensure automated test coverage across unit, integration, security, and schema boundaries.

### 1.2 Completed Features
- **Consent Versioning & Text Hashing:** Server-authoritative text (`1.0.0`) with SHA-256 validation.
- **Consent Endpoints:** `GET /consent/current`, `POST /consent/accept`, `POST /consent/withdraw`.
- **Session Lifecycle Endpoints:** `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/complete`, `POST /sessions/{id}/cancel`.
- **Database Architecture:** `ScreeningConsent`, `ScreeningSession`, and `ScreeningAuditEvent` models with Alembic migration `003_screening_consent_and_session.py`.
- **Concurrency & State Machine Controls:** 409 Conflict on concurrent active sessions, 400 Bad Request on illegal state transitions.
- **IDOR & Security Boundaries:** 404 on unowned sessions; strict role isolation for shopkeepers and unverified optometrists.
- **Frontend Screening UI:** `ConsentScreen.tsx`, `ScreeningIntroScreen.tsx`, `ActiveSessionScreen.tsx`, `SessionHistoryScreen.tsx`, and state controller `apps/mobile/app/screening/index.tsx`.
- **Shared Contracts:** TypeScript types and Zod-compatible validation rules in `shared/types/screening.ts` and `shared/validation/screening.ts`.
- **Atomic Refresh Token Rotation (Phase 2.1 Follow-up):** Verified and implemented `SessionRepository.rotate_and_create` for single-transaction atomic token rotation.

### 1.3 Incomplete or Deferred Features
- **Specific Clinical Vision Tests (Visual Acuity, Color Vision, Astigmatism):** Intentionally scoped for Phase 3.2, 3.3, and 3.4.
- **Optometrist Clinical Referral & Session Review:** Intentionally deferred to Phase 4 (Clinical Review & Provider Dashboard).

---

## 2. Repository Changes

### 2.1 Files Created
- `backend/app/models/screening_consent.py` (SQLAlchemy Declarative Model for Consent)
- `backend/app/models/screening_session.py` (SQLAlchemy Declarative Model for Sessions)
- `backend/app/models/screening_audit_event.py` (SQLAlchemy Declarative Model for Audit Trail)
- `backend/app/schemas/screening.py` (Pydantic v2 validation models)
- `backend/app/repositories/screening_repository.py` (Database access & transaction management)
- `backend/app/services/screening_service.py` (Business logic, hashing, state transitions)
- `backend/app/api/v1/screening.py` (FastAPI route controllers)
- `backend/migrations/versions/003_screening_consent_and_session.py` (Alembic migration)
- `backend/tests/unit/test_screening_unit.py` (Unit tests for consent hash, status enum, schemas)
- `backend/tests/api/test_screening_api.py` (Integration & security tests for screening APIs)
- `shared/types/screening.ts` (TypeScript interfaces and types)
- `shared/validation/screening.ts` (Validation helpers)
- `apps/mobile/src/features/screening/ConsentScreen.tsx` (React Native Consent Review Screen)
- `apps/mobile/src/features/screening/ScreeningIntroScreen.tsx` (Intro & Preparation Screen)
- `apps/mobile/src/features/screening/ActiveSessionScreen.tsx` (Active Session Management Screen)
- `apps/mobile/src/features/screening/SessionHistoryScreen.tsx` (Session Timeline Screen)
- `apps/mobile/app/screening/index.tsx` (Screening workflow navigation orchestrator)
- `docs/backend/PHASE_3_1_CONSENT_ARCHITECTURE.md` (Consent and session lifecycle architecture)
- `docs/backend/PHASE_3_1_API_REFERENCE.md` (Complete OpenAPI / curl endpoint documentation)
- `docs/backend/PHASE_3_1_SECURITY_REVIEW.md` (Threat analysis, IDOR, and security review)
- `docs/phase-reports/PHASE_3_1_REPORT.md` (This master completion report)

### 2.2 Files Modified
- `backend/app/models/user.py`: Added SQLAlchemy relationships for `consents` and `screening_sessions`.
- `backend/app/models/__init__.py`: Registered `ScreeningConsent`, `ScreeningSession`, `ScreeningAuditEvent`.
- `backend/app/core/exceptions.py`: Added domain exceptions: `ConsentRequiredException`, `InvalidConsentVersionException`, `SessionAlreadyActiveException`, `InvalidSessionTransitionException`.
- `backend/app/middleware/error_handler.py`: Added HTTP status code mappings for the new domain exceptions.
- `backend/app/api/v1/router.py`: Mounted `/screening` router.
- `backend/app/repositories/session_repo.py`: Implemented single-transaction `rotate_and_create`.
- `backend/app/services/auth_service.py`: Integrated `rotate_and_create` in `AuthService.refresh`.
- `apps/mobile/src/services/apiClient.ts`: Added token state management and all 8 screening API client methods.

---

## 3. Implementation Details

```mermaid
flowchart TD
    subgraph Client Layer [Cross-Platform Client (React Native / Expo)]
        ScreeningNav["app/screening/index.tsx"]
        ConsentUI["ConsentScreen.tsx"]
        IntroUI["ScreeningIntroScreen.tsx"]
        ActiveUI["ActiveSessionScreen.tsx"]
        HistoryUI["SessionHistoryScreen.tsx"]
        ScreeningNav --> ConsentUI
        ScreeningNav --> IntroUI
        ScreeningNav --> ActiveUI
        ScreeningNav --> HistoryUI
        ApiClient["services/apiClient.ts"]
        ScreeningNav --> ApiClient
    end

    subgraph API Gateway [FastAPI /api/v1/screening]
        ApiClient --> EndpointConsent["/consent/current, /accept, /withdraw"]
        ApiClient --> EndpointSession["/sessions, /sessions/{id}, /complete, /cancel"]
    end

    subgraph Domain Logic [Screening Service & Repository]
        EndpointConsent --> ScreeningSvc["ScreeningService"]
        EndpointSession --> ScreeningSvc
        ScreeningSvc --> HashCheck["SHA-256 Hash Validator"]
        ScreeningSvc --> StateGuard["State Transition Guard"]
        ScreeningSvc --> ConcurrencyGuard["Single-Active Concurrency Guard"]
        ScreeningSvc --> ScreeningRepo["ScreeningRepository"]
    end

    subgraph Data Tier [PostgreSQL / SQLite]
        ScreeningRepo --> DBConsents[("screening_consents")]
        ScreeningRepo --> DBSessions[("screening_sessions")]
        ScreeningRepo --> DBAudit[("screening_audit_events")]
    end
```

### 3.1 Database Migration Details
The Alembic migration `003_screening_consent_and_session.py` defines:
- `screening_consents`: Tracks `id`, `user_id`, `version`, `agreed_at`, `is_active`, `withdrawn_at`, `ip_address`, `user_agent`, `document_hash`.
- `screening_sessions`: Tracks `id`, `user_id`, `status` (`in_progress`, `completed`, `cancelled`), `started_at`, `completed_at`, `cancelled_at`, `cancellation_reason`, `device_info`, `notes`.
- `screening_audit_events`: Immutable audit trail tracking `id`, `user_id`, `event_type`, `resource_type`, `resource_id`, `details`, `ip_address`, `user_agent`, `created_at`.
- Forward-only, dialect-aware index creation compatible with PostgreSQL and SQLite.

### 3.2 Non-Diagnostic Boundary Enforcement
The implementation enforces the following clinical boundaries:
- Enums and schemas reject any medical terms such as `diagnosed`, `prescribed`, `refraction_result`, `cylinder_power`.
- Consent text explicitly warns users: *"OptiGuide is a preliminary vision screening and guidance platform. It does NOT provide a medical diagnosis, medical treatment, or ophthalmic prescription."*
- Every completed screening session contains purely objective screening records; final results advise professional eye examination.

---

## 4. Testing and Verification

### 4.1 Commands Executed & Real Results

| Step | Command | Result | Pass/Fail |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite** | `backend/.venv/Scripts/python -m pytest backend/tests -v --tb=short` | 111 passed, 38 warnings | **PASS** |
| **Ruff Code Formatting** | `backend/.venv/Scripts/ruff format backend` | 64 files left unchanged | **PASS** |
| **Ruff Code Linting** | `backend/.venv/Scripts/ruff check backend` | All checks passed (0 errors) | **PASS** |
| **Database Migration Upgrade** | `backend/.venv/Scripts/alembic upgrade head` | Applied `003_screening_consent_and_session` | **PASS** |
| **Database Migration Rollback** | `backend/.venv/Scripts/alembic downgrade -1` | Reverted `003` cleanly | **PASS** |
| **Database Migration Re-apply** | `backend/.venv/Scripts/alembic upgrade head` | Re-applied `003` idempotently | **PASS** |
| **Frontend TypeScript Typecheck** | `npm --workspace=apps/mobile run typecheck` | 0 errors | **PASS** |
| **Frontend Production Web Build** | `npm run frontend:build:web` | Web bundle compiled into `apps/mobile/dist` | **PASS** |
| **Frontend Jest Tests** | `npm run frontend:test` | 3 suites, 13 passed, 0 failed | **PASS** |

### 4.2 Software and Environment Versions
- **OS:** Windows 11 Pro (win32)
- **Python:** 3.13.14 (`backend/.venv`)
- **FastAPI:** 0.115.11
- **SQLAlchemy:** 2.0.38
- **Alembic:** 1.15.1
- **Pytest:** 8.4.2
- **Node.js:** v22.14.0 / npm 10.9.2
- **Expo SDK:** 52.0.46
- **React Native:** 0.76.7

### 4.3 Tests Executed vs Not Executed
- **Executed:**
  - 111 backend unit and API tests in `backend/tests/` (100% passed).
  - 13 frontend Jest tests in `apps/mobile/__tests__/` (100% passed).
  - Full TypeScript validation of the mobile app.
  - Full Web export build with Expo CLI.
  - SQLite database migration up/down/up cycle.
- **Not Executed:**
  - PostgreSQL live server migration (mocked in SQLite during local Windows test execution; full PostgreSQL driver Psycopg 3 verified in pyproject.toml and migration DDL written to standard SQL).
  - Physical iOS and Android device hardware deployment (tested via Expo Web build and TypeScript type-checking).

---

## 5. Known Issues & Technical Debt

1. **Starlette Deprecation Warnings:**
   - Pytest output noted `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated` and `'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated`. These do not affect functionality and will be addressed in future minor framework upgrades.
2. **ESLint Workspace CLI Script:**
   - Running `npm run lint` reported `'eslint' is not recognized`. Linting is currently enforced via TypeScript strict checks and `ruff` on the backend. Adding `eslint` dev dependency to mobile workspace will be organized in future frontend tooling sprint.
3. **Professional Session Delegations:**
   - Optometrists and shopkeepers currently cannot view any patient screening sessions (returning 404). In Phase 4, a dedicated referral/delegation authorization table will allow patients to share completed screening summaries with verified optometrists.

---

## 6. Phase Acceptance Checklist Verification (Section 18)

- [x] **1. Consent Model & Registry:** `ScreeningConsent` table and model implemented with version, text hash, user tracking, and active boolean.
- [x] **2. Session Model & Enum:** `ScreeningSession` model implemented with `IN_PROGRESS`, `COMPLETED`, `CANCELLED` statuses.
- [x] **3. Audit Event Model:** `ScreeningAuditEvent` implemented with event types, metadata JSON, and client attribution.
- [x] **4. Alembic Migration 003:** Created, verified forward, backward, and re-applied cleanly.
- [x] **5. Single Active Session Constraint:** Enforced in `ScreeningService` and `ScreeningRepository`; returns 409 Conflict.
- [x] **6. Allowed State Transitions:** Enforced strictly (`IN_PROGRESS` $\to$ `COMPLETED` / `CANCELLED`).
- [x] **7. Forbidden Diagnostic States:** Strictly no `DIAGNOSED` or `PRESCRIBED` statuses or prescription schemas.
- [x] **8. SHA-256 Consent Integrity:** Hardcoded server text, version `1.0.0`, verified with unit test.
- [x] **9. Idempotent Consent Acceptance:** Calling accept multiple times returns existing active consent.
- [x] **10. Withdrawal Cascade:** Withdrawing consent cancels active `IN_PROGRESS` sessions.
- [x] **11. Eight Screening Endpoints:** Fully implemented, mounted under `/api/v1/screening`, and tested.
- [x] **12. IDOR Prevention:** Verified that accessing another user's session returns 404 NOT_FOUND.
- [x] **13. Role Isolation:** Verified shopkeepers and unverified optometrists cannot access patient sessions.
- [x] **14. Frontend Screens:** `ConsentScreen`, `ScreeningIntroScreen`, `ActiveSessionScreen`, `SessionHistoryScreen` implemented.
- [x] **15. Frontend Routing:** `apps/mobile/app/screening/index.tsx` orchestrates state and navigation.
- [x] **16. API Client Integration:** `apiClient.ts` updated with token management and all 8 methods.
- [x] **17. Shared Contracts:** `shared/types/screening.ts` and `shared/validation/screening.ts` created.
- [x] **18. Four Documentation Deliverables:**
  - `docs/backend/PHASE_3_1_CONSENT_ARCHITECTURE.md`
  - `docs/backend/PHASE_3_1_API_REFERENCE.md`
  - `docs/backend/PHASE_3_1_SECURITY_REVIEW.md`
  - `docs/phase-reports/PHASE_3_1_REPORT.md`
- [x] **19. Quality Gates:** 111 backend tests passing, 0 ruff errors, 0 TypeScript errors, clean web build.

---

## 7. Next Phase Handoff (Phase 3.2)

### 7.1 Completed Prerequisites for Phase 3.2
- Active consent gating mechanism is established and verified.
- Session lifecycle and single-active-session concurrency are in place.
- Audit logging pipeline is active.
- Frontend routing and session controller are operational.

### 7.2 Proposed Scope for Phase 3.2: Visual Acuity Screening Foundation
1. **Tumbling E / Landolt C Acuity Engine:**
   - Mathematical optotype sizing based on physical display DPI and user distance (40cm near vs. 2m-3m distance screening).
   - Distance calibration using device camera or standardized credit card scaling.
2. **Interactive Acuity Stepping Algorithm:**
   - Adaptive staircase testing algorithm (LogMAR / Snellen progression).
   - Left eye (OS), Right eye (OD), and Both eyes (OU) screening sequence.
3. **Session Result Storage:**
   - Associating visual acuity test run data with the active `ScreeningSession`.
   - Clear non-diagnostic score presentation (e.g. "Preliminary Acuity Estimate: 20/25; Not an Eyeglass Prescription").
