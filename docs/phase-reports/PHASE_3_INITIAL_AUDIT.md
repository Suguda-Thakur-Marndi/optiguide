# OptiGuide — Phase 3 Initial Architecture & Implementation Audit

**Document:** `docs/phase-reports/PHASE_3_INITIAL_AUDIT.md`  
**Phase:** Phase 3.0 (Master Initial Audit)  
**Date:** November 3, 2026  
**Audience:** Principal Software Architect, Senior Full-Stack Engineer, Clinical Safety Engineer, Security Engineer, QA Automation Engineer  
**Status:** **AUDIT COMPLETE**  

---

## 1. Executive Summary

This initial audit establishes the exact source-level state of the OptiGuide repository prior to executing Phase 3. It inspects all backend components, frontend applications (`apps/web` and `apps/mobile`), shared TypeScript contracts (`shared`), and database migrations (`backend/migrations/`).

The audit verifies what features are already functional, identifies exact contract discrepancies and architectural gaps, and specifies the implementation plan for delivering the complete Phase 3 scope:
- Canonical Consent & Screening Session Management.
- Distance & Near Visual Acuity Screening (with physical calibration).
- Astigmatism Dial Screening.
- Pseudoisochromatic Color Vision Screening.
- Clinical assessment database persistence and Alembic migration.
- Full web and mobile integration with zero mock fallbacks.

---

## 2. Source-Level Backend Audit

### 2.1 Application Entry & Routing
- **Entry point:** `backend/app/main.py`
  - Initializes FastAPI with title `"OptiGuide API"`, version `1.0.0`.
  - CORS middleware configured with dynamic regex: `allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"`.
  - Global exception handlers for `AppException`, `RequestValidationError`, and unhandled internal exceptions.
  - Mounts API v1 router under `/api/v1` via `backend/app/api/v1/router.py`.
- **Registered Routers:**
  - `health` (`/health`, `/health/db`)
  - `auth` (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/logout-all`)
  - `users` (`/users/me`, `PATCH /users/me`, `/users/me/sessions`, `PATCH /users/{id}/status`, `/users/clinical/review-access`)
  - `screening` (`/screening/consent/current`, `/screening/consent/accept`, `/screening/consent/withdraw`, `/screening/sessions`)

### 2.2 Database Models & Alembic State
- **Active Migrations (`backend/migrations/versions/`):**
  - `001_initial_baseline.py`: Baseline initialization.
  - `002_user_and_auth.py`: `users` and `refresh_tokens` tables.
  - `003_screening_consent_and_session.py`: `screening_consents`, `screening_sessions`, and `screening_audit_events` tables.
- **Existing Models (`backend/app/models/`):**
  - `User`: UUID primary key, email, password hash (Argon2id), full name, role (`patient`, `shopkeeper`, `optometrist`, `admin`), active/verified flags.
  - `RefreshToken`: UUID primary key, hashed token (SHA-256), revocation flag, expiration, user foreign key.
  - `ScreeningConsent`: UUID, user_id, consent_version, consent_text_hash, is_active, accepted_at, withdrawn_at.
  - `ScreeningSession`: UUID, user_id, consent_id, status (`in_progress`, `completed`, `cancelled`), timestamps, cancellation_reason.
  - `ScreeningAuditEvent`: Immutable audit trail for consent decisions and lifecycle events.

### 2.3 Gaps & Discrepancies in Backend
1. **Clinical Assessment Results Tables Missing:**
   - The database currently lacks dedicated relational models for storing discrete clinical test attempts:
     - Visual Acuity (distance Snellen fractions, logMAR, decimal, tested distance, unassisted/corrected, near reading N-scale).
     - Astigmatism (meridian, uniform clarity observation, axis indication).
     - Color Vision (plates presented, correct count, deficiency type).
     - Calibration metadata (screen dimensions, viewing distance, physical mm scaling, confidence score).
2. **Contract Route Discrepancies:**
   - Consent document route: Backend router defines `GET /screening/consent/current`. Some client versions attempt `GET /screening/consent`.
   - Consent acceptance payload: `ConsentAcceptRequest` expects `version`. Some client calls pass `consent_version`.
   - Clinical review access: Backend defines `GET /users/clinical/review-access`. Web clients historically checked `GET /users/me/clinical-review-access`.

---

## 3. Source-Level Frontend Audit

### 3.1 Web Client (`apps/web`)
- **Stack:** React 18.3.1, Vite 5.4.21, TypeScript 5.3.3.
- **Pages & Components:**
  - `LandingPage.tsx`: Hero overview, 5-minute protocol description, interactive demo preview.
  - `ScreeningFlowPage.tsx`: 8-step screening wizard (intro consent, readiness, symptoms questionnaire, distance Tumbling E, near vision reading, astigmatism fan, color plates, PD estimation).
  - `ResultsPage.tsx`: Detailed observation breakdown, referral recommendation banners, printable report.
  - `EyewearPage.tsx`: Frame try-on and recommendation catalogue.
  - `ShopDashboardPage.tsx`: Optical kiosk management for rural vision centers.
  - `AdminDashboardPage.tsx`: Telemetry and health diagnostics.
  - `AuthModal.tsx`: User registration, login, profile view, profile update, session audit list.
- **API Client (`apps/web/src/services/apiClient.ts`):**
  - Centralized client with token rotation and 401 interceptor.
  - Lacks dedicated methods for submitting discrete clinical assessment results (`acuity`, `astigmatism`, `color-vision`) to the backend.

### 3.2 Mobile Client (`apps/mobile`)
- **Stack:** React Native 0.76.6, Expo SDK 52.0.0, Expo Router 4.0.15, TypeScript 5.3.3.
- **Routes & Screens:**
  - `app/(auth)/login.tsx`: Native authentication view.
  - `app/profile/index.tsx`: Profile inspection and session management.
  - `app/screening/index.tsx`: Native screening flow entry.
  - `src/features/screening/`: Acuity, consent, and session components.
- **API Client (`apps/mobile/src/services/apiClient.ts`):**
  - Connects to `EXPO_PUBLIC_API_URL` (or `http://localhost:8000` / `http://10.0.2.2:8000`).
  - Supports authentication and session creation. Needs assessment submission methods.

### 3.3 Shared Contracts (`shared`)
- **Package:** `@optiguide/shared`
- **Current Types:**
  - `shared/types/screening.ts`: Defines `ScreeningSession`, `DistanceVisionResult`, `NearVisionResult`, `AstigmatismResult`, `ColorVisionResult`, `PDEstimationResult`.
  - Needs updated DTO contracts matching the canonical backend schemas for assessment submission.

---

## 4. Discovered API Contract Discrepancies & Reconciliation Plan

| Area | Current Inconsistency | Reconciliation Decision | Canonical Route / Field |
|---|---|---|---|
| **Clinical Review Access** | `/users/clinical/review-access` vs `/users/me/clinical-review-access` | Support canonical `/users/clinical/review-access` and provide backward-compatible alias `/users/me/clinical-review-access` | `GET /api/v1/users/clinical/review-access` |
| **Current Consent Document** | `/screening/consent/current` vs `/screening/consent` | Support canonical `/screening/consent/current` and provide backward-compatible alias `/screening/consent` | `GET /api/v1/screening/consent/current` |
| **Consent Acceptance Field** | `version` vs `consent_version` | Allow either `version` or `consent_version` in Pydantic `ConsentAcceptRequest` via `validation_alias` | Accepts both; outputs `consent_version` |
| **Screening Session Creation** | Strict empty `{}` vs optional device metadata | Allow optional `device_info` and `notes` metadata without breaking strict validation | `POST /api/v1/screening/sessions` accepts `{ "device_info": {...}, "notes": "..." }` |
| **Assessment Submission** | Non-existent endpoints for sub-tests | Implement discrete sub-resource endpoints under `/screening/sessions/{id}/` | `POST .../acuity`, `POST .../astigmatism`, `POST .../color-vision` |

---

## 5. Clinical Safety & Physical Calibration Requirements

### 5.1 Physical Calibration Safeguards
1. **Screen Sizing & Visual Angle:**
   - Standard Snellen 20/20 optotypes subtend 5 arcminutes of visual angle at the designated viewing distance.
   - At 0.6 m viewing distance: $h = 2 \times 600 \times \tan(5' / 2) \approx 0.873 \text{ mm}$.
   - At 2.0 m viewing distance: $h \approx 2.909 \text{ mm}$.
   - The system must capture device physical DPI or pixel calibration factor.
   - If calibration cannot be verified (e.g. unknown browser DPI), mark the assessment as **`uncalibrated_experimental`** and notify the participant.
2. **Non-Diagnostic Medical Limiter:**
   - Every report and screen must state:
     > *"OptiGuide is a preliminary vision screening tool and cannot independently diagnose refractive error or prescribe lens power. Comprehensive examination by a licensed optometrist or ophthalmologist is required."*
3. **Astigmatism Protocol:**
   - Radial clock/fan dial: Checks meridian asymmetry. Does not output cylinder power or axis prescription.
4. **Color Vision Protocol:**
   - Pseudoisochromatic plate discrimination. Evaluates red-green discrimination. Does not declare definitive genetic classification without clinical control.

---

## 6. Implementation Plan & Target Files

### Stage 1: API Reconciliation & Core Consent Updates
- `backend/app/api/v1/screening.py`: Add route aliases (`/consent`), handle dual-naming.
- `backend/app/api/v1/users.py`: Add alias for `/me/clinical-review-access`.
- `backend/app/schemas/screening.py`: Pydantic aliases for `version` / `consent_version`.

### Stage 2: Clinical Assessment Models & Database Migration
- `backend/app/models/screening_assessment.py`: Create models:
  - `VisualAcuityAssessment`
  - `AstigmatismAssessment`
  - `ColorVisionAssessment`
- `backend/migrations/versions/004_screening_clinical_assessments.py`: Create migration for assessment tables.
- Update `backend/app/models/__init__.py`.

### Stage 3: Assessment Repositories, Schemas & Services
- `backend/app/schemas/clinical_assessments.py`: Pydantic request/response schemas for acuity, astigmatism, color vision, and calibration.
- `backend/app/repositories/screening_repo.py`: Add assessment persistence methods.
- `backend/app/services/screening_service.py`: Scoring algorithms, Snellen calculations, validation, and session linkage.

### Stage 4: API Endpoints for Clinical Assessments
- Extend `backend/app/api/v1/screening.py`:
  - `POST /sessions/{id}/acuity` & `GET /sessions/{id}/acuity`
  - `POST /sessions/{id}/astigmatism` & `GET /sessions/{id}/astigmatism`
  - `POST /sessions/{id}/color-vision` & `GET /sessions/{id}/color-vision`
  - `GET /sessions/{id}/summary` (Comprehensive clinical session summary)

### Stage 5: Shared Contracts & Frontend API Client Expansion
- Update `shared/types/screening.ts` and `shared/index.ts`.
- Update `apps/web/src/services/apiClient.ts` with typed methods.
- Update `apps/mobile/src/services/apiClient.ts`.

### Stage 6: Frontend Workflow Integration
- Integrate backend assessment submission in `apps/web/src/pages/ScreeningFlowPage.tsx`.
- Update `apps/web/src/pages/ResultsPage.tsx` to read persisted results from backend.
- Update `apps/mobile/src/features/screening/`.

### Stage 7: Testing, Security Review & Reporting
- Comprehensive Pytest suite (`backend/tests/api/test_clinical_screening_api.py`, `backend/tests/unit/test_clinical_scoring.py`).
- Automated frontend tests in web and mobile.
- Security review (`docs/phase-reports/PHASE_3_SECURITY_REVIEW.md`).
- Master phase reports (`PHASE_3_1_...`, `PHASE_3_2_...`, `PHASE_3_3_...`, `PHASE_3_FINAL_COMPLETION_REPORT.md`).

---

## 7. Audit Sign-off

The repository audit is complete. All architectural foundations and gaps are verified. Implementation proceeds directly to Stage 1.
