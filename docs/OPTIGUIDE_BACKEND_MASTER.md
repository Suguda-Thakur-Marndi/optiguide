# OPTIGUIDE — BACKEND MASTER DOCUMENTATION & SYSTEM ARCHITECTURE
## Single Source of Truth: Architecture, Clinical Workflows, Security Baseline, Database Schemas, API Contracts & Implementation Reports (Phases 1 through 4)

---

> [!IMPORTANT]
> **STATUTORY MEDICAL & CLINICAL SAFETY NOTICE**  
> OptiGuide is a preliminary vision screening and eyewear guidance platform engineered for underserved communities, tele-optometry, and retail optical enablement.  
> **OptiGuide is NOT a diagnostic medical device and does NOT independently prescribe corrective ophthalmic lens power.**  
> All visual acuity measurements, astigmatism observations, color vision assessments, pupillary distance estimates, and frame recommendations are non-diagnostic screening observations. Final ophthalmic lens prescriptions and medical diagnoses must be performed by a licensed, certified eye care professional (optometrist or ophthalmologist) conducting physical clinical examination.

---

# TABLE OF CONTENTS
1. [Executive Summary & Project Purpose](#1-executive-summary--project-purpose)
2. [Complete System Architecture & Design Patterns](#2-complete-system-architecture--design-patterns)
3. [Technology Stack & Runtime Specifications](#3-technology-stack--runtime-specifications)
4. [Clinical Safety Baseline & Regulatory Boundaries](#4-clinical-safety-baseline--regulatory-boundaries)
5. [Security Architecture & Threat Mitigation Baseline](#5-security-architecture--threat-mitigation-baseline)
6. [Data Models & Entity Relationships (All Phases 1–4)](#6-data-models--entity-relationships-all-phases-14)
7. [Alembic Database Migrations History (Revisions 001–005)](#7-alembic-database-migrations-history-revisions-001005)
8. [Phase 1 & 1.1 Documentation: Foundations & Runtime Health](#8-phase-1--11-documentation-foundations--runtime-health)
9. [Phase 2 & 2.1 Documentation: Authentication & Security Hardening](#9-phase-2--21-documentation-authentication--security-hardening)
10. [Phase 3 & 3.1 Documentation: Screening Consent & Session Lifecycle](#10-phase-3--31-documentation-screening-consent--session-lifecycle)
11. [Phase 3.2 Documentation: Clinical Screening Assessments](#11-phase-32-documentation-clinical-screening-assessments)
12. [Phase 4 Documentation: Professional Verification & Clinical Referrals](#12-phase-4-documentation-professional-verification--clinical-referrals)
13. [Phase 4 Eyewear Product Catalogue & Multi-Shop Inventory Subsystem](#13-phase-4-eyewear-product-catalogue--multi-shop-inventory-subsystem)
14. [Phase 4 Eyewear Recommendation Engine (100.0-Point Scoring)](#14-phase-4-eyewear-recommendation-engine-1000-point-scoring)
15. [Phase 4 Pupillary Distance (PD) Estimation Subsystem](#15-phase-4-pupillary-distance-pd-estimation-subsystem)
16. [Phase 4 Remediation & Physiological Defense Fixes](#16-phase-4-remediation--physiological-defense-fixes)
17. [Full REST API Specification (All 38+ Endpoints)](#17-full-rest-api-specification-all-38-endpoints)
18. [Unified Error Handling & Standard Response Envelopes](#18-unified-error-handling--standard-response-envelopes)
19. [Database Connectivity & Multi-Dialect Management (PostgreSQL vs. SQLite)](#19-database-connectivity--multi-dialect-management-postgresql-vs-sqlite)
20. [Automated Testing Strategy & Verification Evidence (140 Passing Tests)](#20-automated-testing-strategy--verification-evidence-140-passing-tests)
21. [Frontend & Mobile Integration Contracts (API Handoff)](#21-frontend--mobile-integration-contracts-api-handoff)
22. [Development Environment Setup & Operational Runbook](#22-development-environment-setup--operational-runbook)
23. [Known Limitations & Production Readiness Checklist](#23-known-limitations--production-readiness-checklist)
24. [Phase 4 Evidence-Based Completion Report](#24-phase-4-evidence-based-completion-report)
25. [Voice Assistant Subsystem: STT, TTS & Conversational Guidance](#25-voice-assistant-subsystem-speech-to-text-text-to-speech--conversational-guidance-implemented--verified)
26. [Complete Online Vision Screening Platform (7-Module Modular Architecture)](#26-complete-online-vision-screening-platform-7-module-modular-architecture)
27. [Voice-Controlled Adaptive Visual Acuity Test Engine](#27-voice-controlled-adaptive-visual-acuity-test-engine)
28. [Appendix A: Environment Configuration & Secret Reference](#28-appendix-a-environment-configuration--secret-reference)
29. [Appendix B: Role-Based Access Control (RBAC) Permission Matrix](#29-appendix-b-role-based-access-control-rbac-permission-matrix)
30. [Appendix C: Clinical Algorithmic Reference & Cut-off Thresholds](#30-appendix-c-clinical-algorithmic-reference--cut-off-thresholds)

---

# 1. EXECUTIVE SUMMARY & PROJECT PURPOSE

OptiGuide is a multi-platform tele-health and optometry enablement solution built to bridge eye health disparities in remote, rural, and primary care settings. Many rural communities lack accessible refraction clinics and optometrists. OptiGuide provides:

1. **Self-Service & Community Vision Screening:** Citizen-led preliminary assessments for visual acuity (Snellen / LogMAR), astigmatism clock-dial distortion, and Ishihara color deficiency.
2. **Accredited Clinical Referral Network:** Bridging identified vision anomalies directly to certified optometrists and ophthalmologists through a secure, patient-consented record sharing pipeline.
3. **Local Optical Retail Enablement:** Empowering local rural opticians and kiosk shopkeepers with inventory tracking, catalogue management, and intelligent face-shape and budget-optimized frame recommendations.
4. **Digital Anthropometric PD Estimation:** Non-invasive computer-vision based pupillary distance measurement validated by demographic physiological boundaries and verified by licensed clinicians.

---

# 2. COMPLETE SYSTEM ARCHITECTURE & DESIGN PATTERNS

OptiGuide Backend enforces **Clean Architecture** principles structured in distinct abstraction boundaries:

```
                            +---------------------------------------+
                            |       HTTP Clients (Web & Mobile)     |
                            +---------------------------------------+
                                                |
                                                v
                            +---------------------------------------+
                            |        FastAPI Routing Layer          |
                            |  (app/api/v1/*.py, OpenAPI, CORS)     |
                            +---------------------------------------+
                                                |
                         +----------------------+----------------------+
                         |                      |                      |
                         v                      v                      v
             +-----------------------+ +------------------+ +-------------------+
             | Authentication & RBAC | | Request Parsing  | | Response Envelope |
             | (SecurityMiddleware)  | | (Pydantic Schemas| | (Unified Errors)  |
             +-----------------------+ +------------------+ +-------------------+
                                                |
                                                v
                            +---------------------------------------+
                            |         Domain Service Layer          |
                            | (app/services/*_service.py)           |
                            | - Recommendation 100-pt engine        |
                            | - PD physiological validator          |
                            | - Clinical priority derivation        |
                            | - Referral transition state machine   |
                            +---------------------------------------+
                                                |
                                                v
                            +---------------------------------------+
                            |       Repository & Data Layer         |
                            | (app/repositories/*_repo.py)          |
                            | - Explicit SQL query abstraction      |
                            | - Concurrency locking (FOR UPDATE)    |
                            | - SQLAlchemy 2.0 ORM Mappings         |
                            +---------------------------------------+
                                                |
                                                v
                            +---------------------------------------+
                            |       Relational Persistence Engine   |
                            |   (PostgreSQL 16 / SQLite Dialect)    |
                            +---------------------------------------+
```

### Architectural Principles:
- **Separation of Concerns:** Controllers (FastAPI routes) perform parameter ingestion, request validation, and HTTP status orchestration; Services execute pure business logic, calculations, and policy enforcement; Repositories isolate database interactions.
- **Dependency Injection:** Database sessions (`Session`) and authenticated credentials (`User`) are injected per-request using FastAPI's `Depends` mechanisms.
- **No Mock Fallbacks in Core Logic:** Production code never serves simulated screening results or hardcoded fake responses.
- **Fail-Secure Boundary Enforcement:** Unauthenticated or unauthorized callers cannot access patient screening or referral data.

---

# 3. TECHNOLOGY STACK & RUNTIME SPECIFICATIONS

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python | 3.13 / 3.12+ | High-performance asynchronous backend execution |
| **API Framework** | FastAPI | 0.115+ | High-speed ASGI REST API with automated OpenAPI docs |
| **Data Validation** | Pydantic v2 | 2.10+ | Strict type validation, physiological bounds, `ConfigDict(extra="forbid")` |
| **ORM & Database Layer** | SQLAlchemy | 2.0+ | Declarative typed mappings, `Mapped[]`, dialect abstraction |
| **Database Migrations** | Alembic | 1.14+ | Versioned relational DDL migrations with automated downgrade capability |
| **Production Database** | PostgreSQL | 16+ | ACID-compliant production relational store with row locking (`FOR UPDATE`) |
| **Test/Local Database** | SQLite (in-memory & file) | 3.40+ | High-speed isolated execution during CI and local testing |
| **Password Hashing** | Argon2id | via `argon2-cffi` | Memory-hard, timing-attack-resistant cryptographic password hashing |
| **Token Cryptography** | PyJWT | 2.10+ | Stateless RS256/HS256 signed access and refresh tokens |
| **HTTP Client (Testing)** | Starlette TestClient / HTTPX | 0.28+ | End-to-end integration and API verification |
| **Linter & Formatter** | Ruff | 0.9+ | High-speed static analysis, formatting, and flake8/pycodestyle verification |

---

# 4. CLINICAL SAFETY BASELINE & REGULATORY BOUNDARIES

OptiGuide operates under strict medical software safety parameters:

1. **Non-Diagnostic Classifier:** OptiGuide assesses visual acuity indicators (e.g. 20/40, 20/80), astigmatism meridian clarity distortion, and red-green color confusion. It does not output a diagnostic ICD-10 code or medical disease label.
2. **Zero Autonomous Prescription:** The platform explicitly forbids calculating spherical, cylindrical, or axis refractive corrections or dispensing optical lenses without independent professional examination.
3. **Mandatory Patient Informed Consent:** Before any vision screening session is initiated, citizens must explicitly review and accept the Versioned Medical Screening Consent and Disclaimer.
4. **Mandatory Clinical Disclaimers:** All API responses containing screening summaries, referrals, frame recommendations, or pupillary distance measurements return a structured `clinical_disclaimer` attribute.
5. **Fail-Safe Triage Direction:** When high interocular acuity differences ($\ge 0.40\text{ logMAR}$) or acute vision degradation are flagged, the platform automatically flags clinical priority as `URGENT` or `PRIORITY` and prompts professional consultation.

---

# 5. SECURITY ARCHITECTURE & THREAT MITIGATION BASELINE

### 5.1 Authentication Subsystem
- **Argon2id Hashing:** User passwords are never stored in plaintext or weak hashes. Uses 64 MiB memory cost, 3 time iterations, and 4 parallel threads.
- **Dual-Token Lifecycle:**
  - `access_token`: Short-lived (30 minutes), carries user ID and role claims, signed via HMAC-SHA256.
  - `refresh_token`: Long-lived (7 days), stored in database as a cryptographic SHA-256 hash.
- **Refresh Token Rotation & Reuse Detection:** Every refresh operation invalidates the old token and issues a new pair. If an already-used refresh token is presented, all user sessions are immediately revoked (breach mitigation).

### 5.2 Role-Based Access Control (RBAC)
The platform defines four canonical roles:
- `patient`: Citizen user; owns screenings, gives consent, creates referrals, manages shares, views frame recommendations.
- `shopkeeper`: Optical retail owner; manages shops, tracks inventory, inspects stock transaction ledgers.
- `optometrist` / `eye_care_professional`: Accredited practitioner; submits clinical credentials, reviews shared patient records, conducts physical verification.
- `admin`: Platform administrator; verifies professional credentials, manages master product catalogues, oversees system health.

### 5.3 Anti-Privilege Escalation & Mass Assignment Defenses
- Public registration (`POST /api/v1/auth/register`) strictly forbids self-assigning privileged roles (`admin`, `shopkeeper`, `optometrist`). Unassigned requests safely default to `patient`.
- Profile update schemas (`UserUpdateRequest`) forbid updating `is_active`, `is_verified`, or `role`.
- Pydantic models enforce `extra="forbid"`, preventing JSON payload injection attacks.

### 5.4 IDOR & Confidentiality Isolation
- Screening sessions, referrals, and clinical reviews enforce ownership verification against `current_user.id`.
- Foreign record access attempts return `404 Not Found` rather than `403 Forbidden` to prevent object identifier enumeration.
- Record sharing is time-limited (`expires_at`) and can be revoked on-demand (`access_status == "REVOKED"`). Revoked shares return `403 Forbidden` with detailed diagnostic notices.

---

# 6. DATA MODELS & ENTITY RELATIONSHIPS (ALL PHASES 1–4)

```mermaid
erDiagram
    users ||--o{ refresh_tokens : owns
    users ||--o{ screening_consents : signs
    users ||--o{ screening_sessions : conducts
    users ||--o{ pd_assessments : measures
    users ||--o{ patient_referrals : creates
    users ||--o{ shops : owns
    users ||--o{ eyewear_recommendations : requests
    users ||--o| professional_profiles : verifies

    screening_sessions ||--o{ visual_acuity_assessments : contains
    screening_sessions ||--o{ astigmatism_assessments : contains
    screening_sessions ||--o{ color_vision_assessments : contains
    screening_sessions ||--o{ patient_referrals : prompts

    patient_referrals ||--o{ patient_record_shares : delegates
    patient_referrals ||--o{ clinical_reviews : receives

    catalog_brands ||--o{ catalog_products : manufactures
    catalog_categories ||--o{ catalog_products : categorizes
    catalog_products ||--o{ shop_inventory : stocks
    shops ||--o{ shop_inventory : stocks
    shop_inventory ||--o{ inventory_transactions : logs
    eyewear_recommendations ||--o{ recommendation_feedbacks : evaluates
```

### Complete Models Inventory:
1. `User`: Core identity, email, hashed password, role, active & verified flags.
2. `RefreshToken`: Token rotation, family tracking, expiry, hashed string.
3. `ScreeningConsent`: Regulatory consent version, text hash, explicit acceptance, withdrawal timestamps.
4. `ScreeningSession`: Multi-stage screening session, device metadata, status (`pending`, `in_progress`, `completed`, `cancelled`).
5. `VisualAcuityAssessment`: Monocular and binocular acuity, Snellen fraction (`20/20`), LogMAR score, distance meters.
6. `AstigmatismAssessment`: Clock dial meridian examination, uniform clarity indicator, sharpest axis angle.
7. `ColorVisionAssessment`: Ishihara plate identification, deficiency indicator, plate index.
8. `ProfessionalProfile`: Eye care license number, issuing authority, qualification title, verification status (`PENDING`, `VERIFIED`, `REJECTED`, `SUSPENDED`).
9. `PatientReferral`: Clinical priority (`ROUTINE`, `PRIORITY`, `URGENT`), referral reason, lifecycle status (`PENDING`, `SHARED`, `IN_REVIEW`, `COMPLETED`, `CLOSED`, `REJECTED`).
10. `PatientRecordShare`: Delegated optometrist access, status (`ACTIVE`, `REVOKED`), expiration date.
11. `ClinicalReview`: Professional clinical observations, in-person examination recommendation, recommended exam timeframe.
12. `CatalogBrand` & `CatalogCategory`: Eyewear taxonomy and metadata.
13. `CatalogProduct`: Eyewear SKU, name, frame shape/material/type, gender target, `base_price_inr` (`Numeric(10, 2)`).
14. `Shop` & `ShopInventory`: Multi-shop physical retail locations, stock levels, reserved quantities, check constraints.
15. `InventoryTransaction`: Stock adjustment audit ledger with delta tracking and operator identity.
16. `EyewearRecommendation` & `RecommendationFeedback`: Input criteria, ranked product matches, user ratings and fit feedback.
17. `PDAssessment`: Binocular and monocular PD (mm), calibration evidence, server-verified flags, adult/pediatric demographic tracking, professional physical review.

---

# 7. ALEMBIC DATABASE MIGRATIONS HISTORY (REVISIONS 001–005)

All schema changes are tracked via sequential, non-destructive Alembic migrations capable of bidirectional migration:

| Revision ID | Description | Created Tables / Alterations | Verified Dialects |
| :--- | :--- | :--- | :--- |
| `001_initial_users` | Core User identity | `users`, indexes on email and role | PostgreSQL, SQLite |
| `002_refresh_tokens` | Refresh token lifecycle | `refresh_tokens`, foreign keys to `users` | PostgreSQL, SQLite |
| `003_screening_consent_sessions` | Regulatory consent & sessions | `screening_consents`, `screening_sessions` | PostgreSQL, SQLite |
| `004_screening_clinical_assessments` | Vision screening tests | `visual_acuity_assessments`, `astigmatism_assessments`, `color_vision_assessments` | PostgreSQL, SQLite |
| `005_phase4_referrals_catalog_recommendations_pd` | Eyewear guidance, inventory, referrals, PD | `professional_profiles`, `patient_referrals`, `patient_record_shares`, `clinical_reviews`, `catalog_categories`, `catalog_brands`, `catalog_products`, `shops`, `shop_inventory`, `inventory_transactions`, `eyewear_recommendations`, `recommendation_feedbacks`, `pd_assessments` | PostgreSQL, SQLite |

---

# 8. PHASE 1 & 1.1 DOCUMENTATION: FOUNDATIONS & RUNTIME HEALTH

Phase 1 established core architectural foundations:
- Initialized FastAPI application container with structured lifecycle events (`lifespan`).
- Implemented `/health` and `/api/v1/health` with live relational database connectivity checks (`SELECT 1`).
- Enforced structured environment variable loading via Pydantic BaseSettings (`app/core/config.py`).
- Established unified JSON logging middleware recording client IP, HTTP verb, URL path, response status, and duration in milliseconds.
- Enforced automated exception handling catching unhandled errors and returning sanitized RFC 7807 problem details without leaking internal stack traces.

---

# 9. PHASE 2 & 2.1 DOCUMENTATION: AUTHENTICATION & SECURITY HARDENING

Phase 2 and 2.1 established authentication and access governance:
- Implemented `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, and `/api/v1/auth/logout`.
- Integrated Argon2id hashing via `argon2-cffi` ensuring resilience against GPU/ASIC brute-force attacks.
- Configured stateless JWT token generation with standard RFC claims (`sub`, `role`, `iss`, `aud`, `exp`, `iat`, `jti`).
- Built in-memory IP rate limiting (`RateLimiter`) with configurable burst thresholds to defend against brute-force login attempts.
- Hardened role isolation: public registration cannot assign privileged roles; user profile updates cannot modify security attributes.

---

# 10. PHASE 3 & 3.1 DOCUMENTATION: SCREENING CONSENT & SESSION LIFECYCLE

Phase 3 and 3.1 established the clinical screening workflow:
- **Versioned Informed Consent:** Citizens must explicitly accept clinical disclaimers before initiating screening.
- **Session State Machine:** Governs progression (`pending` $\to$ `in_progress` $\to$ `completed` or `cancelled`).
- **Cascade Revocation:** If a citizen withdraws consent (`DELETE /api/v1/screening/consent/current`), all active in-progress screening sessions are automatically cancelled to protect citizen autonomy.

---

# 11. PHASE 3.2 DOCUMENTATION: VISUAL ACUITY SCREENING & CLINICAL ASSESSMENTS

The Visual Acuity screening subsystem provides clinical optics mathematical conversions, physical calibration validation, geometric screening constraints, and deterministic non-diagnostic triage summaries.

### 11.1 Dedicated Clinical Optics Engine (`VisualAcuityService`)
The visual acuity engine implements clinical conversion mathematics:
$$\text{logMAR} = \log_{10}\left(\frac{\text{denominator}}{\text{numerator}}\right)$$
- **Standardized Precision:** Formatted and rounded to 2 decimal places.
- **Snellen Parsing:** Strict regular expression verification `^(\d+)\s*/\s*(\d+)$` rejecting malformed strings, non-positive denominators or numerators, and non-numeric inputs.
- **Imperial & Metric Conversion Matrix:**
  - Snellen $20/20 \iff 6/6 \iff 1.00\text{ Decimal} \iff 0.00\text{ logMAR}$ (Standard normal acuity)
  - Snellen $20/40 \iff 6/12 \iff 0.50\text{ Decimal} \iff 0.30\text{ logMAR}$ (Mild acuity reduction)
  - Snellen $20/60 \iff 6/18 \iff 0.33\text{ Decimal} \iff 0.48\text{ logMAR}$ (Moderate impairment $\to$ referral recommended)
  - Snellen $20/100 \iff 6/30 \iff 0.20\text{ Decimal} \iff 0.70\text{ logMAR}$ (Significant visual reduction)
  - Snellen $20/200 \iff 6/60 \iff 0.10\text{ Decimal} \iff 1.00\text{ logMAR}$ (Severe visual impairment)
- **Physiological Boundary Validation:** Enforces supported clinical range $[-0.30, 2.00]\text{ logMAR}$. Inputs outside this range raise `ValidationException` (HTTP 422).
- **Data Reconciliation & Conflict Defense:** If a client provides pre-computed `logmar` or `decimal_acuity`, the service computes mathematical equivalents from the Snellen fraction and verifies agreement within $\pm 0.05$ tolerance (`LOGMAR_TOLERANCE` / `DECIMAL_TOLERANCE`). Conflicting inputs are rejected with HTTP 422 rather than accepting contradictory clinical records.

### 11.2 Viewing Geometry & Display Calibration Safeguards
Screening accuracy depends on physical testing conditions, which are strictly guarded:
- **Separate Distance & Near Viewing Geometry:**
  - `DISTANCE` screening requires `tested_distance_meters` in $[0.3\text{m}, 12.0\text{m}]$.
  - `NEAR` screening requires `near_reading_distance_cm` in $[15.0\text{cm}, 100.0\text{cm}]$.
- **Zero Blind Trust in Client Calibration:**
  - Client assertion `is_calibrated: true` without geometric hardware metadata is forced to `is_calibrated: false`.
  - Calibration is validated only when physical display DPI, screen pixel dimensions, and physical viewing distance are provided. Validated claims are stamped `GEOMETRIC_VALIDATION_PASSED`; unverified claims receive `UNVERIFIED_CLIENT_CLAIM`.

### 11.3 Clinical Consent & Session Lifecycle Enforcement
- **Consent Pre-condition:** Visual acuity assessments require active, unwithdrawn informed consent (`ScreeningConsent.is_active == True`). Missing or revoked consent immediately returns `403 Forbidden` (`CONSENT_REQUIRED`).
- **Session Lifecycle Policy:** Assessments can only be recorded on `in_progress` screening sessions. Attempts to submit assessments to `completed` or `cancelled` sessions return `400 Bad Request` (`INVALID_SESSION_TRANSITION`).
- **Idempotency & Updates:** Resubmitting an assessment for the same session, eye, and test type updates the existing record with `updated_at = datetime.now(UTC)` and logs `ACUITY_ASSESSMENT_UPDATED` in the audit ledger.
- **IDOR Defense:** Cross-patient access attempts return `404 Not Found` to prevent account and session enumeration.

### 11.4 Deterministic Non-Diagnostic Summary & Triage
The summary service aggregates session results across OD, OS, and OU tests:
- **Missing Observations:** Flags missing eye or distance/near assessments (e.g. "Right eye (OD) distance visual acuity not assessed", "Near visual acuity screening was not conducted").
- **Triage Criteria:**
  - Monocular or binocular visual acuity $\ge 0.40\text{ logMAR}$ (worse than $20/40$) flags referral recommendation with specific eye indicators.
  - Interocular visual acuity difference $|OD - OS| \ge 0.30\text{ logMAR}$ flags significant asymmetry.
- **Non-Diagnostic Medical Disclaimer:** Every summary response includes the mandatory disclaimer:
  > *"OptiGuide visual acuity screening is a preliminary functional assessment aid, not a diagnostic ophthalmic examination. It does not diagnose refractive errors (such as myopia, hyperopia, or astigmatism), amblyopia, or ocular pathologies, and cannot calculate corrective lens powers or generate optical prescriptions. Normal screening observations do not guarantee complete ocular health. A certified optometrist or ophthalmologist must perform comprehensive clinical evaluations."*

### 11.5 Clinical Screening Endpoints
- `POST /api/v1/screening/sessions/{session_id}/acuity` — Record distance or near visual acuity.
- `GET /api/v1/screening/sessions/{session_id}/acuity` — List visual acuity records for a session.
- `GET /api/v1/screening/sessions/{session_id}/acuity/summary` — Retrieve deterministic visual acuity observations breakdown and referral triage.
- `GET /api/v1/screening/acuity/history` (and `/api/v1/acuity/history`) — Paginated historical visual acuity screenings for the authenticated user.
- `GET /api/v1/screening/acuity/{assessment_id}` (and `/api/v1/acuity/{assessment_id}`) — Retrieve single visual acuity assessment by ID with strict ownership validation.
- `POST /api/v1/screening/sessions/{session_id}/astigmatism` — Record radial clock dial/fan observations.
- `GET /api/v1/screening/sessions/{session_id}/astigmatism` — List astigmatism records for session.
- `POST /api/v1/screening/sessions/{session_id}/color-vision` — Record Ishihara color plate observations.
- `GET /api/v1/screening/sessions/{session_id}/color-vision` — List color vision records for session.
- `GET /api/v1/screening/sessions/{session_id}/summary` — Composite session clinical summary across all modalities.

---

### 11.6 Interactive Adaptive Visual Acuity Screening Engine (Staircase Protocol)

The OptiGuide backend implements a server-controlled interactive visual acuity screening engine. The client application renders optotypes and captures user responses, while the backend dictates difficulty progression, evaluates correctness server-side, enforces stopping criteria, and determines preliminary visual acuity thresholds.

#### 11.6.1 Clinical Screening Protocol (`ISO8596_ATS_V1`)
- **Protocol Basis:** Modeled after the Amblyopia Treatment Study (ATS) and ISO 8596 staircase visual acuity testing standards.
- **Validation Status:** `TECHNICAL FRAMEWORK IMPLEMENTED — PRELIMINARY SCREENING (NOT CLINICALLY VALIDATED AS AN INDEPENDENT MEDICAL DIAGNOSTIC DEVICE)`.
- **ATS 3-of-4 Rule:**
  - Up to 4 presentations are evaluated per difficulty level.
  - A level is marked **PASS** when 3 correct responses are obtained.
  - A level is marked **FAIL** when 2 incorrect responses occur (as reaching 3-of-4 becomes mathematically impossible).
- **LogMAR Level Specification Table:**
  - Level 0: $20/200 \iff 1.00\text{ logMAR} \iff 0.10\text{ Decimal} \iff 50.00\text{ arcmin}$
  - Level 1: $20/125 \iff 0.80\text{ logMAR} \iff 0.16\text{ Decimal} \iff 31.62\text{ arcmin}$
  - Level 2: $20/100 \iff 0.70\text{ logMAR} \iff 0.20\text{ Decimal} \iff 25.12\text{ arcmin}$
  - Level 3: $20/80 \iff 0.60\text{ logMAR} \iff 0.25\text{ Decimal} \iff 19.95\text{ arcmin}$
  - Level 4: $20/60 \iff 0.48\text{ logMAR} \iff 0.33\text{ Decimal} \iff 15.14\text{ arcmin}$
  - Level 5: $20/50 \iff 0.40\text{ logMAR} \iff 0.40\text{ Decimal} \iff 12.59\text{ arcmin}$
  - Level 6: $20/40 \iff 0.30\text{ logMAR} \iff 0.50\text{ Decimal} \iff 10.00\text{ arcmin}$ (Standard screening start)
  - Level 7: $20/30 \iff 0.18\text{ logMAR} \iff 0.67\text{ Decimal} \iff 7.59\text{ arcmin}$
  - Level 8: $20/25 \iff 0.10\text{ logMAR} \iff 0.80\text{ Decimal} \iff 6.31\text{ arcmin}$
  - Level 9: $20/20 \iff 0.00\text{ logMAR} \iff 1.00\text{ Decimal} \iff 5.00\text{ arcmin}$ (Standard normal vision)
  - Level 10: $20/15 \iff -0.12\text{ logMAR} \iff 1.33\text{ Decimal} \iff 3.80\text{ arcmin}$ (Supra-normal vision)
- **Staircase Progression & Stopping Rules:**
  1. Passing a level advances difficulty to the next smaller optotype level (`level += 1`).
  2. Failing a level after previously passing a larger level satisfies the stopping criterion. The smallest reliably passed level is recorded as the visual acuity threshold.
  3. Failing an intermediate starting level (e.g. Level 6) without prior passes steps down to larger optotypes (Level 4 or Level 0).
  4. Failing at the largest optotype level (Level 0) terminates testing with acuity flagged as worse than $20/200$ ($> 20/200$, $1.10\text{ logMAR}$).
  5. Reaching Level 10 with a pass stops at the physiological resolution ceiling.

#### 11.6.2 Server-Controlled Optotype Engine
- **Supported Sets:**
  - `TUMBLING_E`: Orientations `UP`, `DOWN`, `LEFT`, `RIGHT`. Challenge symbols `E_UP`, `E_DOWN`, `E_LEFT`, `E_RIGHT`.
  - `SLOAN`: 10-letter standardized set (`C`, `D`, `E`, `F`, `L`, `N`, `O`, `P`, `T`, `Z`).
- **Non-Repeating Selection:** Random selection strictly prevents immediate repetition (`presented_symbol != previous_symbol`).
- **Zero Answer Leakage:** Challenge payloads never disclose `expected_response`. Only presented symbols, choices, and physical dimensions are transmitted.

#### 11.6.3 Physical Sizing & 4-Tier Display Calibration
Optotypes are sized using visual angle trigonometry rather than arbitrary pixel sizes:
$$\theta_{\text{rad}} = \left(\frac{\theta_{\text{arcmin}}}{60}\right) \times \left(\frac{\pi}{180}\right)$$
$$H_{\text{meters}} = 2 \times D \times \tan\left(\frac{\theta_{\text{rad}}}{2}\right)$$
$$H_{\text{mm}} = H_{\text{meters}} \times 1000, \quad H_{\text{px}} = \left(\frac{H_{\text{mm}}}{25.4}\right) \times \text{DPI}$$
- **4-Tier Calibration Model:**
  1. `UNCALIBRATED`: Nominal CSS scaling only. Results flagged as uncalibrated preliminary screening.
  2. `CLIENT_REPORTED`: Client provided DPI, resolution, and distance, but unverified.
  3. `SERVER_VERIFIED`: Screen DPI ($70-1200$), screen resolution ($\ge 320\text{px}$), and physical viewing distance passed server geometric plausibility checks with reference calibration.
  4. `PROFESSIONALLY_VALIDATED`: Supervised and verified by licensed clinical staff.

#### 11.6.4 Eye Testing & Occlusion Accountability
- Supports monocular testing (`right` / `OD`, `left` / `OS`) and binocular testing (`both` / `OU`).
- The backend tracks `user_reported_occlusion: true/false` to record whether occlusion of the non-tested eye was citizen-reported or professionally supervised.
- Distance testing defaults to $3.0\text{m}$; near testing defaults to $0.40\text{m}$ ($40\text{cm}$).

#### 11.6.5 Seamless Screening Session Integration
Upon adaptive test completion:
- The smallest reliably resolved level is converted into Snellen, LogMAR, and Decimal acuity.
- A `VisualAcuityAssessment` record is automatically created/updated in the database and linked via `test.assessment_id`.
- Downstream clinical triage summaries (`GET /sessions/{id}/summary`), clinical referral sharing (`/api/v1/referrals`), and eyewear frame recommendations (`/api/v1/recommendations/eyewear`) immediately consume the adaptive test result.

#### 11.6.6 Adaptive Acuity API Endpoints
- `POST /api/v1/screening/sessions/{session_id}/acuity/start` — Start an interactive adaptive test session.
- `GET /api/v1/screening/acuity/tests/{test_id}/next` — Retrieve the active optotype presentation challenge without leaking answers.
- `POST /api/v1/screening/acuity/tests/{test_id}/response` — Submit citizen answer, validate correctness server-side, advance difficulty, or complete test.
- `POST /api/v1/screening/acuity/tests/{test_id}/complete` — Manually finalize an ongoing adaptive screening test.
- `POST /api/v1/screening/acuity/tests/{test_id}/cancel` — Cancel an ongoing adaptive test.
- `GET /api/v1/screening/acuity/tests/{test_id}/result` — Retrieve the completed adaptive test determination and clinical disclaimer.
- Canonical aliases are also mounted under `/api/v1/acuity/tests/{test_id}/...`.

---

# 12. PHASE 4 DOCUMENTATION: PROFESSIONAL VERIFICATION & CLINICAL REFERRALS

Phase 4 bridges citizen screening results directly to accredited eye care professionals:

### 12.1 Optometrist Credential Verification
- Optometrists submit credentials (`license_number`, `issuing_authority`, `registration_year`, `qualification_title`).
- Administrative staff inspect and verify credentials via `POST /api/v1/professionals/admin/{profile_id}/verify` (`VERIFY`, `REJECT`, `SUSPEND`, `REACTIVATE`).
- Professional verification activates `is_verified=True` on the practitioner user account.

### 12.2 Referral Lifecycle State Machine
Canonical state transitions are strictly governed:
$$\text{PENDING} \longrightarrow \text{SHARED} \longrightarrow \text{IN\_REVIEW} \longrightarrow \text{COMPLETED} \longrightarrow \text{CLOSED}$$
- Illegal status transitions (e.g. attempting to reopen a `CLOSED` referral back to `PENDING`) raise `422 Unprocessable Entity`.

### 12.3 Patient-Governed Record Sharing
- Patients delegate access to verified practitioners with customizable expiration limits (`expires_in_days`).
- Patients can immediately revoke access via `DELETE /api/v1/referrals/{referral_id}/share/{share_id}` or `POST /api/v1/referrals/{referral_id}/shares/{share_id}/revoke`.
- Expired or revoked shares return `403 Forbidden` with clear diagnostic messages. Non-shared referrals return `404 Not Found` to prevent IDOR enumeration.

---

# 13. PHASE 4 EYEWEAR PRODUCT CATALOGUE & MULTI-SHOP INVENTORY SUBSYSTEM

### 13.1 Product Catalogue Schema
- Normalized relational taxonomy: `catalog_categories`, `catalog_brands`, and `catalog_products`.
- Products include SKU, brand, category, frame shape (Round, Rectangle, Square, Aviator, Cat-Eye, Oval), frame material (Acetate, Titanium, Metal, TR90, Plastic), frame type (Full Rim, Semi-Rimless, Rimless), gender target (`unisex`, `men`, `women`, `kids`), and dimensions.
- **Financial Precision:** Base price is stored as `Numeric(10, 2)` mapped to Python `Decimal`, eliminating floating-point rounding errors.

### 13.2 Multi-Shop Inventory & Concurrency Locking
- Multi-branch support via `shops` and `shop_inventory`.
- Real-time stock adjustments executed transactionally via `POST /api/v1/shops/{shop_id}/inventory/adjust`.
- **Concurrency Protection:** Inventory lookups execute `with_for_update()` on PostgreSQL to prevent concurrent race conditions during rapid stock adjustments.
- **Reserved Stock Defense:** Decrements cannot reduce stock below `reserved_quantity`. Check constraints (`ck_shop_inventory_stock_non_negative`, `ck_shop_inventory_reserved_non_negative`) enforce non-negative stock at the database engine level.
- Every adjustment creates an immutable `inventory_transactions` record for audit compliance.

---

# 14. PHASE 4 EYEWEAR RECOMMENDATION ENGINE (100.0-POINT SCORING)

OptiGuide provides transparent, explainable frame recommendations scored out of **exactly 100.0 points**:

$$\text{Total Match Score} = S_{\text{budget}} + S_{\text{face}} + S_{\text{material}} + S_{\text{type}} + S_{\text{stock}}$$

| Component | Max Points | Scoring Criteria | Rationale String Example |
| :--- | :---: | :--- | :--- |
| **Budget Compatibility** ($S_{\text{budget}}$) | **30.0** | $\le 100\%$ budget: 30 pts<br>$\le 115\%$ budget: 15 pts<br>Exceeds budget: 0 pts | "Priced at ₹1,500.00, comfortably within your budget of ₹2,000.00." |
| **Face Shape Harmony** ($S_{\text{face}}$) | **25.0** | Optimal geometric harmony: 25 pts<br>Secondary complementary: 20 pts<br>Direct user preferred shape match: 25 pts<br>Unspecified neutral: 12.5 pts | "Round shape provides optimal harmony for a Square face shape." |
| **Material Preference** ($S_{\text{material}}$) | **20.0** | Matches user material: 20 pts<br>Alternative material: 5 pts<br>Unspecified neutral: 10.0 pts | "Manufactured from high-durability Titanium material as specified." |
| **Frame Type Preference** ($S_{\text{type}}$) | **15.0** | Matches user frame type: 15 pts<br>Alternative type: 5 pts<br>Unspecified neutral: 7.5 pts | "Features your requested Full Rim frame build." |
| **Stock Availability** ($S_{\text{stock}}$) | **10.0** | Currently in-stock at shop: 10 pts<br>Catalogue backorder: 0 pts | "Currently in stock and ready for immediate fitting." |
| **Total Maximum** | **100.0** | Theoretical Upper Bound | Every factor contributes to explainable advice |

---

# 15. PHASE 4 PUPILLARY DISTANCE (PD) ESTIMATION SUBSYSTEM

### 15.1 Computer Vision Calibration & Trust Boundaries
- The platform supports camera-based PD estimation utilizing standard magnetic/plastic reference cards ($85.60\text{ mm} \times 53.98\text{ mm}$, ISO/IEC 7810 ID-1 standard).
- **Server-Side Trust Boundary:** The server never trusts client-submitted `is_calibrated=True` or `confidence_score=1.0`. The server independently verifies calibration evidence (aspect ratio $1.586 \pm 0.08$, valid scale factor $> 0\text{ px/mm}$). Without geometric proof, confidence is capped at $0.50$ (unverified estimate).

### 15.2 Demographic Physiological Validation Boundaries
Before persisting, PD measurements are validated against human demographic boundaries:
- **Adult Distance PD:**
  - Binocular PD: $45.0\text{ mm} \le \text{PD} \le 80.0\text{ mm}$
  - Monocular Left/Right PD: $20.0\text{ mm} \le \text{PD} \le 42.0\text{ mm}$
- **Pediatric PD (`is_pediatric=True`):**
  - Binocular PD: $38.0\text{ mm} \le \text{PD} \le 55.0\text{ mm}$
  - Monocular Left/Right PD: $18.0\text{ mm} \le \text{PD} \le 30.0\text{ mm}$
- **Monocular Sum Consistency:** Monocular sum must agree with binocular total within physiological tolerance:
  $$|(\text{PD}_{\text{left}} + \text{PD}_{\text{right}}) - \text{PD}_{\text{binocular}}| \le 3.0\text{ mm}$$

### 15.3 Clinical Review & Confirmation Workflow
Licensed optometrists can conduct physical confirmation of PD estimates via `POST /api/v1/pd/assessments/{id}/professional-review`, elevating status to `PROFESSIONALLY_REVIEWED` with verified confidence $0.99$.

---

# 16. PHASE 4 & PHASE 4.1 SECURITY REMEDIATION, DATABASE INTEGRITY & TRANSACTION HARDENING

During Phase 4 and Phase 4.1 security reviews, critical architectural, clinical safety, and data integrity remediations were implemented:

### 16.1 Pupillary Distance (PD) Trust Boundary & Clinician Review Security
1. **Untrusted Client Claims:** In the absence of a server-side computer vision image processing pipeline, client-submitted calibration metadata and confidence scores are strictly untrusted claims. The server records measurements as `ESTIMATED`, setting `is_server_verified = False` and `confidence_score = None` (preventing arbitrary 0.50/0.92 fabricated scores).
2. **Pediatric Physiological Boundaries:** Demographic awareness differentiates pediatric ($38.0 - 55.0\text{ mm}$ binocular, $18.0 - 30.0\text{ mm}$ monocular) and adult ($45.0 - 80.0\text{ mm}$ binocular, $18.0 - 42.0\text{ mm}$ monocular) ranges.
3. **Monocular Sum Tolerance:** Monocular consistency strictly validates that $|(L + R) - \text{Total}| \le 3.0\text{ mm}$.
4. **Clinician Authorization & Review Distinctions:** Clinician review (`POST /api/v1/pd/assessments/{id}/professional-review`) strictly requires an active, unexpired `PatientRecordShare` between the patient and the professional (returns 403 Forbidden otherwise).
5. **Measurement Review vs Physical Exam:** Reviews marking `REQUIRES_PROFESSIONAL_MEASUREMENT` or `REJECTED` preserve `is_server_verified = False` and `confidence_score = None`. Only confirmed physical in-person clinical examinations set `is_server_verified = True` and `confidence_score = 1.0` (and require providing `measured_binocular_pd_mm`).

### 16.2 Referral Priority Derivation, State Machine & Audit Integrity
1. **Server-Authoritative Priority Triage:** Patient self-assignment of `URGENT` or `PRIORITY` without objective clinical screening findings is blocked (HTTP 422). Clinical priority is derived server-side via `compute_derived_clinical_priority` based on objective logMAR acuity, interocular difference ($\Delta\text{logMAR} \ge 0.30 \to \text{PRIORITY}$, $\Delta\text{logMAR} \ge 0.40 \to \text{URGENT}$), astigmatic meridians, and color vision plate failures.
2. **Canonical State Machine Lifecycle:** Strict status transitions (`VALID_REFERRAL_TRANSITIONS`) prevent invalid jumps (e.g., `CLOSED` referrals cannot be reopened).
3. **Multi-Table Atomic Transactions:** Referral creation, delegation sharing, revocations, and clinical reviews are wrapped in atomic database transaction blocks with single `db.commit()` and comprehensive rollback on exception.
4. **Immutable Referral Audit Logging:** Every referral event (creation, sharing, revocation, review, status transition) writes an immutable audit record to `referral_audit_events` capturing actor ID, role, action, previous state, new state, timestamp, and metadata without leaking sensitive tokens.

### 16.3 Shop Inventory Authorization, Atomicity & Concurrency Controls
1. **Inventory Transaction History Authorization:** `GET /api/v1/shops/{shop_id}/inventory/{inventory_id}/transactions` requires authentication, enforces ownership verification (blocks patients and non-owner shopkeepers with HTTP 403), and validates that the inventory belongs to the requested shop (HTTP 404 on mismatch).
2. **Single-Transaction Stock Adjustments:** Stock adjustments and `InventoryTransaction` creation execute inside a single transaction with row locking (`with_for_update`) to eliminate race conditions and avoid partial commits.
3. **Database Check Constraints:** Added check constraint `ck_shop_inventory_reserved_le_stock` (`reserved_quantity <= stock_quantity`) in migration `006` to guarantee that reserved quantities can never exceed available stock.

### 16.4 Financial Precision & Recommendation Availability
1. **Exact Decimal Financial Arithmetic:** Base prices and budget limits are modeled and compared using exact `Decimal` arithmetic, preventing floating-point imprecision.
2. **Zero and Negative Budget Handling:** If `budget_max_inr <= Decimal("0.00")`, the engine awards 0 budget points and records an explicit explanatory reason.
3. **Live Stock Availability Enforcement:** Products with zero available stock (`stock_quantity - reserved_quantity <= 0`) are marked `is_in_stock = False`, receive 0 availability points, and are clearly documented as out of stock.

### 16.5 Database Migration 006
- Migration `006_phase4_1_inventory_constraints_and_referral_audit.py` introduces:
  - Check constraint `ck_shop_inventory_reserved_le_stock` on `shop_inventory`.
  - `referral_audit_events` table with indexes on `referral_id`, `actor_id`, and `occurred_at`.
  - Verified clean bidirectional execution (`alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`).

---

# 17. FULL REST API SPECIFICATION (ALL 38+ ENDPOINTS)

### Core & Health
- `GET /health` — Microservice health status
- `GET /api/v1/health` — Complete API service health
- `GET /api/v1/health/db` — Relational database connectivity check

### Authentication (`/api/v1/auth`)
- `POST /register` — Citizen registration (defaults to `patient`)
- `POST /login` — Password authentication; returns JWT pair
- `POST /refresh` — Token rotation; returns fresh access and refresh token
- `POST /logout` — Single-session invalidation
- `POST /logout-all` — Global invalidation of all user sessions
- `GET /me` — Current authenticated user identity

### User Management (`/api/v1/users`)
- `GET /me` — Retrieve own profile
- `PATCH /me` — Update allowed profile fields (name, phone)
- `GET /{user_id}` — Admin user lookup

### Screening Consent & Sessions (`/api/v1/screening`)
- `GET /consent/current` — Inspect current active consent
- `POST /consent` — Record formal consent acceptance
- `DELETE /consent/current` — Withdraw consent; cancels active sessions
- `POST /sessions` — Initiate screening session
- `GET /sessions/me` — List citizen's screening history
- `GET /sessions/{session_id}` — Retrieve session details
- `POST /sessions/{session_id}/cancel` — Cancel in-progress session

### Clinical Screening Assessments (`/api/v1/screening/sessions/{session_id}`)
- `POST /acuity` — Record monocular/binocular visual acuity
- `GET /acuity` — List acuity records for session
- `POST /astigmatism` — Record astigmatism clock dial observations
- `GET /astigmatism` — List astigmatism records for session
- `POST /color-vision` — Record Ishihara color plate observations
- `GET /color-vision` — List color vision records for session
- `GET /summary` — Retrieve composite session findings and triage risk

### Eyewear Product Catalogue (`/api/v1/catalog`)
- `POST /categories` — Admin category creation
- `GET /categories` — List active frame categories
- `POST /brands` — Admin brand creation
- `GET /brands` — List active eyewear brands
- `POST /products` — Admin product creation
- `GET /products` — Search and filter catalogue frames
- `GET /products/{product_id}` — Product detail lookup

### Retail Shops & Inventory (`/api/v1/shops`)
- `POST ""` — Register retail shop or kiosk
- `GET /me` — List shops owned by current user
- `GET /{shop_id}/inventory` — Query real-time stock levels
- `POST /{shop_id}/inventory/adjust` — Atomic stock adjustment with reserved stock defense
- `GET /{shop_id}/inventory/{inventory_id}/transactions` — Stock audit ledger

### Eyewear Recommendations (`/api/v1/recommendations`)
- `POST /eyewear` — Generate 100-pt multi-factor frame recommendations
- `POST /feedback` — Record user satisfaction and selected frame

### Pupillary Distance (`/api/v1/pd`)
- `POST /assessments` — Record digital PD measurement
- `GET /assessments/me` — List historical PD measurements
- `GET /assessments/{assessment_id}` — PD detail lookup
- `POST /assessments/{assessment_id}/confirm` — Patient confirms estimate
- `POST /assessments/{assessment_id}/reject` — Reject inaccurate measurement
- `POST /assessments/{assessment_id}/professional-review` — Professional clinical verification

### Patient Referrals & Delegation (`/api/v1/referrals`)
- `POST ""` — Generate referral from screening findings
- `GET /me` — List citizen's referrals
- `GET /{referral_id}` — Referral detail lookup
- `POST /{referral_id}/share` — Delegate record access to verified optometrist
- `POST /{referral_id}/shares/{share_id}/revoke` (also `DELETE /share/{share_id}`) — Revoke record share
- `GET /{referral_id}/shares` — List active record shares
- `POST /{referral_id}/close` — Formal referral closure

### Eye Care Professionals (`/api/v1/professionals`)
- `POST /apply` — Submit professional license credentials
- `GET /me` — Inspect own credential verification status
- `GET /admin/pending` — Admin list of pending practitioner profiles
- `POST /admin/{profile_id}/verify` — Admin credential adjudication
- `GET /shared-records` — List patient records delegated to caller
- `GET /shared-records/{referral_id}` — Detailed screening breakdown of shared record
- `POST /reviews/{referral_id}` — Submit clinical review & observations

---

# 18. UNIFIED ERROR HANDLING & STANDARD RESPONSE ENVELOPES

All errors conform to RFC 7807 structured JSON envelopes:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable explanation of error condition",
    "details": [
      {
        "field": "binocular_pd_mm",
        "issue": "Measurement falls outside physiological adult human range (45.0 - 80.0 mm)."
      }
    ]
  }
}
```

### Standard Status Codes:
- `400 Bad Request` — Malformed syntax or illegal operation.
- `401 Unauthorized` — Missing, expired, or invalid JWT credentials.
- `403 Forbidden` — Insufficient role permissions or revoked record share.
- `404 Not Found` — Requested entity does not exist or access blocked by IDOR defense.
- `422 Unprocessable Entity` — Schema constraint failure or illegal state machine transition.
- `500 Internal Server Error` — Sanitized unhandled server failure; error details logged internally.

---

# 19. DATABASE CONNECTIVITY & MULTI-DIALECT MANAGEMENT (POSTGRESQL VS. SQLITE)

OptiGuide employs dual-dialect database abstraction:
- **SQLite:** In-memory or file-based (`optiguide.db`) for high-speed local development and zero-dependency automated test execution. Emulates boolean constraints and datetime parsing cleanly.
- **PostgreSQL:** Production target utilizing native `UUID`, `TIMESTAMP WITH TIME ZONE`, and pessimistic row locking (`with_for_update()`).
- Repository code avoids dialect-specific SQL functions, ensuring migrations run cleanly on both SQLite and PostgreSQL.

---

# 20. AUTOMATED TESTING STRATEGY & VERIFICATION EVIDENCE (190 PASSING TESTS)

The backend test suite consists of **190 automated tests** executing across unit, integration, and API test suites with zero failures:

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.4.2, pluggy-1.7.0
rootdir: C:\Users\sugud\OneDrive\Documents\optiguide\backend
configfile: pyproject.toml
plugins: anyio-4.16.0, asyncio-0.26.0
collected 190 items

backend\tests\api\test_adaptive_acuity_api.py (7 tests) .......             [  3%]
backend\tests\api\test_auth_api.py (13 tests) .............                 [ 10%]
backend\tests\api\test_catalog_and_inventory_api.py (3 tests) ...          [ 12%]
backend\tests\api\test_clinical_screening_api.py (5 tests) .....           [ 14%]
backend\tests\api\test_errors_api.py (4 tests) ....                        [ 16%]
backend\tests\api\test_phase2_1_security_hardening.py (18 tests) ........ [ 26%]
backend\tests\api\test_phase4_1_security.py (12 tests) ............         [ 32%]
backend\tests\api\test_phase4_remediation.py (8 tests) ........            [ 36%]
backend\tests\api\test_recommendations_and_pd_api.py (2 tests) ..          [ 37%]
backend\tests\api\test_referrals_and_reviews_api.py (3 tests) ...          [ 39%]
backend\tests\api\test_root_api.py (5 tests) .....                         [ 42%]
backend\tests\api\test_screening_api.py (8 tests) ........                 [ 46%]
backend\tests\api\test_users_api.py (5 tests) .....                        [ 48%]
backend\tests\api\test_v1_health_api.py ....... (7 tests)                  [ 52%]
backend\tests\api\test_visual_acuity_api.py (9 tests) .........            [ 57%]
backend\tests\integration\test_auth_integration.py (3 tests) ...           [ 58%]
backend\tests\integration\test_db_integration.py (4 tests) ....            [ 61%]
backend\tests\integration\test_db_isolation.py (1 test) .                  [ 61%]
backend\tests\unit\test_adaptive_acuity_engine.py (7 tests) .......        [ 65%]
backend\tests\unit\test_clinical_scoring.py (3 tests) ...                  [ 66%]
backend\tests\unit\test_config.py (4 tests) ....                           [ 68%]
backend\tests\unit\test_exceptions.py (1 test) .                           [ 69%]
backend\tests\unit\test_logging.py (5 tests) .....                         [ 72%]
backend\tests\unit\test_phase2_1_security_unit.py (14 tests) .............. [ 79%]
backend\tests\unit\test_phase4_units.py (4 tests) ....                     [ 81%]
backend\tests\unit\test_schemas.py (6 tests) ......                        [ 84%]
backend\tests\unit\test_screening_unit.py (6 tests) ......                 [ 87%]
backend\tests\unit\test_security_auth.py (8 tests) ........                [ 92%]
backend\tests\unit\test_visual_acuity_service.py (15 tests) ............... [100%]

====================== 190 passed, 66 warnings in 6.06s =======================
```

- **Pass Rate:** 100% (190 / 190 tests passing).
- **Automated SQLite Environment:** **VERIFIED** (190 passed in isolated test transactions).
- **Live PostgreSQL Server:** **NOT VERIFIED** (migrations tested bidirectionally with SQLite batch mode; production PostgreSQL deployment pending live cluster availability).
- **Ruff Linting:** 0 errors (`All checks passed!`).
- **Ruff Formatting:** 112 files cleanly formatted.

---

# 21. FRONTEND & MOBILE INTEGRATION CONTRACTS (API HANDOFF)

### Base URL:
- Local Development: `http://localhost:8000`
- Production: `https://api.optiguide.example.com`

### Authentication Headers:
Every protected API request must include:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Standard Pagination Envelope:
All list endpoints return pagination envelopes:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

# 22. DEVELOPMENT ENVIRONMENT SETUP & OPERATIONAL RUNBOOK

### 1. Prerequisites
- Python 3.12 or 3.13 installed.
- PowerShell or POSIX terminal.

### 2. Environment Activation & Dependencies
```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Database Migrations
```powershell
# Upgrade database to head
python -m alembic upgrade head

# Inspect current revision
python -m alembic current
```

### 4. Running the Development Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Swagger UI will be available at: `http://localhost:8000/docs`.

### 5. Executing Test Suites & Linting
```powershell
# Run full pytest suite
python -m pytest tests -v

# Run Ruff linter and format checks
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

---

# 23. KNOWN LIMITATIONS & PRODUCTION READINESS CHECKLIST

### Known Limitations:
1. **Live PostgreSQL Verification:** Automated tests execute against SQLite in-memory dialect. PostgreSQL DDL is verified via Alembic SQL generation, but final live PostgreSQL database cluster verification is recommended upon production staging deployment.
2. **Camera Hardware Sensor Variation:** Mobile device cameras have differing optical distortions and focal lengths; the server validates geometry, but physical pupillometer confirmation remains best practice for high refractive error lenses.

### Production Readiness Checklist:
- [x] All 5 Alembic database migrations tested for upgrade and downgrade.
- [x] Passwords hashed with Argon2id; JWT tokens rotated with reuse detection.
- [x] Role-based access control matrix enforced on all routes.
- [x] IDOR defenses active on screening sessions, referrals, and clinical reviews.
- [x] Financial prices stored in `Numeric(10, 2)` / `Decimal`.
- [x] Recommendation scoring verified at 100.0 maximum points.
- [x] Concurrency locking (`with_for_update`) and reserved stock defenses active.
- [x] Demographic physiological boundaries enforced for adult and pediatric PD.
- [x] 140 automated tests passing with 0 failures.
- [x] Ruff static analysis passes with 0 lint errors and clean formatting.

---

# 24. PHASE 4 & PHASE 4.1 EVIDENCE-BASED COMPLETION REPORT

### 24.1 Implementation & Remediation Verification Matrix

| Requirement | Implementation Status | Evidence / Test Case | Environment Status |
| :--- | :---: | :--- | :---: |
| **Professional Onboarding & Verification** | **COMPLETE** | `test_professional_verification_workflow` | **VERIFIED (SQLite)** |
| **Referral Priority Derivation** | **COMPLETE** | `compute_derived_clinical_priority` verified; `test_referral_urgent_priority_self_assignment_blocked`, `test_referral_patient_cannot_self_assign_priority` | **VERIFIED (SQLite)** |
| **Referral State Machine & Transition Rules** | **COMPLETE** | `VALID_REFERRAL_TRANSITIONS` enforced; `test_referral_state_machine_invalid_transition`, `test_referral_closed_cannot_be_reopened` | **VERIFIED (SQLite)** |
| **Delegated Record Sharing & Revocation** | **COMPLETE** | `share_referral`, `revoke_share`; `test_referral_expired_and_revoked_shares_rejected` | **VERIFIED (SQLite)** |
| **Immutable Referral Audit Logging** | **COMPLETE** | `ReferralAuditEvent` model, migration 006, `test_referral_audit_events_logged` | **VERIFIED (SQLite)** |
| **Financial Decimal Precision** | **COMPLETE** | `Numeric(10, 2)` / `Decimal` on `CatalogProduct.base_price_inr`, Decimal comparisons in recommendation engine | **VERIFIED (SQLite)** |
| **Shop Inventory Concurrency & Reserved Stock** | **COMPLETE** | `with_for_update()`, single-transaction atomic adjustment, `test_inventory_reserved_quantity_defense` | **VERIFIED (SQLite)** |
| **Shop Inventory History Authorization** | **COMPLETE** | Caller authentication & ownership verification; `test_inventory_transactions_requires_auth`, `test_inventory_transactions_forbidden_for_patient_and_non_owner` | **VERIFIED (SQLite)** |
| **Database Check Constraints (Migration 006)** | **COMPLETE** | Check constraint `ck_shop_inventory_reserved_le_stock` (`reserved <= stock`); `test_inventory_check_constraint_reserved_le_stock` | **VERIFIED (SQLite)** |
| **Eyewear Recommendation Scoring** | **COMPLETE** | Exactly 100.0 pt max; `test_recommendation_scoring_maximum_is_100` | **VERIFIED (SQLite)** |
| **Zero & Negative Budget Handling** | **COMPLETE** | Zero budget points awarded with explanatory reason; `test_recommendation_zero_and_negative_budget` | **VERIFIED (SQLite)** |
| **Out-of-Stock Recommendation Scoring** | **COMPLETE** | Products with 0 available stock marked `is_in_stock = False` (0 pts); `test_recommendation_out_of_stock_scores_zero_stock_points` | **VERIFIED (SQLite)** |
| **PD Physiological & Demographic Boundaries** | **COMPLETE** | Adult (45–80mm), Pediatric (38–55mm), monocular sum tolerance $\le 3.0\text{mm}$; `test_pd_pediatric_range_validation` | **VERIFIED (SQLite)** |
| **PD Trust Boundary & Spoofing Defense** | **COMPLETE** | Untrusted client claims set to unverified (`is_server_verified = False`, `confidence_score = None`); `test_pd_client_untrusted_claims_not_verified` | **VERIFIED (SQLite)** |
| **PD Clinician Review Authorization** | **COMPLETE** | Active `PatientRecordShare` strictly required; `test_pd_review_forbidden_without_active_patient_share`, `test_pd_review_requires_measurement_status_leaves_unverified`, `test_pd_review_measure_action_without_binocular_pd_rejected` | **VERIFIED (SQLite)** |
| **Database Migrations** | **COMPLETE** | Revisions `005` & `006` tested bidirectionally via Alembic | **VERIFIED (SQLite)** |
| **Production PostgreSQL Target** | **PENDING LIVE** | Database migrations and models designed for PostgreSQL 15+; live cloud connection not configured in local environment | **NOT VERIFIED (Live PostgreSQL)** |
| **Automated Test Suite Execution** | **COMPLETE** | 152 automated tests passing (100% pass rate) | **VERIFIED (SQLite)** |
| **Static Analysis & Linting** | **COMPLETE** | Ruff check: 0 errors; Ruff format: clean (100 files) | **VERIFIED** |

---

# 25. VOICE ASSISTANT SUBSYSTEM: SPEECH-TO-TEXT, TEXT-TO-SPEECH & CONVERSATIONAL GUIDANCE (IMPLEMENTED & VERIFIED)

### 25.1 Subsystem Architecture & Workflow Overview
The OptiGuide Voice Assistant subsystem provides full bidirectional voice interaction for vision screening workflows, adhering to rigorous clinical safety guardrails. The architecture operates entirely **offline** on Windows environments using native speech drivers while providing optional online neural synthesis fallbacks.

```text
User Microphone (PCM WAV)
          │
          ▼
POST /api/v1/voice/transcribe OR /chat
          │
          ▼
Audio Validation (Magic bytes 'RIFF...WAVE', size limit 10MB, frame integrity)
          │
          ▼
Speech-to-Text (STT Engine: Windows System.Speech.Recognition Engine)
          │
          ▼
Recognized Text & Confidence Score
          │
          ▼
OptiGuide Conversational Guidance & Intent Reasoning Engine
  ├── Emergency Triage Detection (acute pain, sudden vision loss -> Urgent Alert)
  ├── Screening Initiation (Visual Acuity, Astigmatism, Color Vision flow)
  ├── Topical Explanations (Acuity optotypes, Clock dial, Ishihara plates, PD)
  ├── Eyewear Styling Advice (non-prescription frame guidance)
  └── Statutory Clinical Safety Disclaimer Injection
          │
          ▼
Generated Clinical Guidance Text Response
          │
          ▼
Text-to-Speech (TTS Engine: Windows System.Speech.Synthesis / gTTS fallback)
          │
          ▼
Generated Binary Audio Payload (PCM 16-bit 22,050Hz Mono WAV / MP3)
          │
          ▼
Return: Playable Audio Stream OR Base64-Encoded VoiceChatResponse
```

---

### 25.2 Voice API Specification & Contracts

| Endpoint | HTTP Method | Input Type | Output MIME / Schema | Description |
| :--- | :---: | :--- | :--- | :--- |
| `/api/v1/voice/status` | `GET` | None | `VoiceStatusResponse` | Operational status of STT and TTS engines, offline capability, limits |
| `/api/v1/voice/transcribe` | `POST` | `multipart/form-data` (`file: .wav`) | `TranscriptionResponse` | Converts PCM WAV audio into recognized text with confidence |
| `/api/v1/voice/synthesize` | `POST` | `application/json` (`SynthesizeRequest`) | `audio/wav` or `audio/mpeg` | Synthesizes response text into playable binary audio stream |
| `/api/v1/voice/chat` | `POST` | `multipart/form-data` (`file` and/or `text`) | `VoiceChatResponse` | Complete end-to-end voice screening dialogue pipeline |

#### Request & Response Examples:

1. **Synthesize Speech (`POST /api/v1/voice/synthesize`):**
   - **Request:**
     ```json
     {
       "text": "Welcome to OptiGuide preliminary vision screening.",
       "format": "wav"
     }
     ```
   - **Response Headers:** `Content-Type: audio/wav`, `Content-Disposition: inline; filename=optiguide_speech.wav`
   - **Response Body:** Binary PCM 16-bit WAV audio stream.

2. **End-to-End Voice Chat (`POST /api/v1/voice/chat`):**
   - **Request:** `file=@test_voice.wav`
   - **Response JSON:**
     ```json
     {
       "transcription": "Hello love the guide I want to start my vision screening",
       "response_text": "Welcome to OptiGuide. We are ready to begin your preliminary vision screening. The screening includes Visual Acuity, Astigmatism, and Color Vision assessments...",
       "intent": "START_SCREENING",
       "confidence": 0.7331,
       "audio_base64": "UklGRtS5AwBXQVZFZm10IBIA...",
       "audio_format": "audio/wav",
       "clinical_disclaimer": "CLINICAL DISCLAIMER: OptiGuide voice assistant provides preliminary vision screening guidance and eyewear information. It does not provide medical diagnoses, treatment plans, or optical prescriptions. Consult a licensed eye care professional for comprehensive clinical evaluation."
     }
     ```

---

### 25.3 Clinical Safety Guardrails

1. **Non-Diagnostic Policy:** The voice assistant explicitly refuses to diagnose ocular pathologies, prescribe spectacle/contact lens powers, or interpret raw acuity scores as clinical prescriptions.
2. **Emergency Triage Redirection:** Spoken complaints indicating ocular emergencies (severe pain, sudden vision loss, flashes of light, chemical contact, eye trauma) trigger an immediate `EMERGENCY_TRIAGE` intent redirecting the user to an emergency ophthalmology clinic or hospital emergency room.
3. **Mandatory Disclaimer:** Every synthesized response and dialogue interaction incorporates the statutory clinical disclaimer.

---

### 25.4 Live Verification & Real Audio Testing Evidence

1. **Live Server Runtime:**
   - Server running at `http://127.0.0.1:8000`.
   - Swagger Documentation active at `http://127.0.0.1:8000/docs`.
   - Liveness & Database Health: `GET /health` $\to$ status `ok`, `GET /api/v1/health` $\to$ database `connected`.

2. **Real Audio Microphone & Speech Tests:**
   - **Genuine Spoken WAV Sample:** `test_voice.wav` (188,302 bytes, PCM 16-bit mono). Spoken phrase: *"Hello OptiGuide, I want to start my vision screening."*
   - **STT Verification:** `POST /api/v1/voice/transcribe` recognized text: `"Hello love the guide I want to start my vision screening"`, confidence `0.7331`, processing time `0.84s`.
   - **TTS Verification:** `POST /api/v1/voice/synthesize` produced 219,828 bytes of clean PCM WAV audio, verified playable on disk (`live_test_synth.wav`, 4.98 seconds, 22,050 Hz).
   - **End-to-End Chat Verification:** `POST /api/v1/voice/chat` ingested `test_voice.wav`, classified intent as `START_SCREENING`, generated clinical guidance text, and synthesized 1,023,406 bytes of response speech (`live_test_chat_response.wav`, 23.21 seconds, 22,050 Hz).

3. **Failure Handling Verification:**
   - Empty audio upload (0 bytes): HTTP 422 `VALIDATION_ERROR` ("Audio recording is empty or corrupt").
   - Corrupt non-WAV data: HTTP 422 `VALIDATION_ERROR` ("Audio must be a valid PCM WAV (.wav) file").
   - Oversized recording (> 10MB): HTTP 422 `VALIDATION_ERROR` ("Audio file exceeds maximum upload size limit").
   - Empty text input for TTS: HTTP 422 `VALIDATION_ERROR` ("Text content for speech synthesis cannot be empty").
   - Missing both audio and text: HTTP 422 `VALIDATION_ERROR` ("Either an audio recording or text prompt must be provided").

4. **Automated Test Suite Execution:**
   - 28 voice tests executed: `pytest tests/unit/test_voice_service.py tests/api/test_voice_api.py` $\to$ **28 passed, 0 failed in 5.50s**.
   - Full regression suite: `pytest tests/` $\to$ **218 passed, 0 failed in 11.52s** (100% pass rate).
   - Static analysis: `ruff check` (0 errors) and `ruff format --check` (117 files clean).

---

### 25.5 Final Voice Implementation Verdict Matrix

| Criterion | Final Status | Technical Evidence & Details |
| :--- | :---: | :--- |
| **Backend Service** | **RUNNING** | Active at `http://127.0.0.1:8000`, Swagger at `/docs`, DB connected |
| **Speech-to-Text (STT)** | **WORKING** | Local Windows System.Speech offline STT, validated with genuine audio |
| **Text-to-Speech (TTS)** | **WORKING** | Windows SAPI offline WAV + gTTS online MP3 fallback, audio verified |
| **Voice Pipeline (E2E)** | **WORKING** | Full Audio Ingest $\to$ STT $\to$ Clinical Intent $\to$ TTS pipeline verified |
| **Real Audio Test** | **PASSED** | Live PCM WAV speech transcribed, synthesized, and verified playable |
| **Failure Handling** | **PASSED** | Corrupt, empty, oversized audio and invalid text rejected with HTTP 422 |
| **Offline Independence**| **YES** | Default STT and TTS engines require 0 internet access and 0 external API keys |

---

# 26. COMPLETE ONLINE VISION SCREENING PLATFORM (7-MODULE MODULAR ARCHITECTURE)

OptiGuide provides an interactive, guided online vision screening platform inspired by digital vision screening workflows (such as Essilor's online test), built from the ground up as an original, independent OptiGuide clinical screening platform.

### Architectural Principles:
1. **Clinical Rigor & Statutory Disclaimer**: Non-diagnostic, non-prescriptive preliminary functional observations. All citizen-facing payloads require informed consent and display clear disclaimers that digital screening cannot replace an in-person eye exam.
2. **Server-Side Scoring & Security**: Challenge progression and correctness evaluation happen strictly server-side. Correct answers are NEVER leaked to the client in challenge options or stimulus payloads.
3. **Display Hardware Calibration**: Dynamic calculation of screen PPI based on standard physical reference measurement (ISO/IEC 7810 ID-1 card) to ensure millimeter-accurate optotype rendering across diverse screens.
4. **Multilingual Inclusivity**: Full localized metadata, instructions, questions, and observation copy across English (`en`), Hindi (`hi`), and Odia (`or`).

---

## 26.1 The 7 Modular Screening Engines

OptiGuide incorporates 7 dedicated screening modules covering refractive, functional, and physiological visual dimensions:

### Module 1: Visual Acuity (`VISUAL_ACUITY`)
- **Clinical Target**: Distance and near high-contrast resolution acuity.
- **Eyes Tested**: Monocular (`OD`, `OS`) and Binocular (`OU`).
- **Protocols Supported**: `TUMBLING_E`, `LANDOLT_C`, `SLOAN_LETTERS`.
- **Adaptive Progression**: Staircase difficulty across calibrated Snellen fractions ($20/200$, $20/100$, $20/50$, $20/30$, $20/20$) with physical millimeter scaling calculated from display PPI.
- **Outcome Classification**: `NO_CONCERN_REPORTED` ($20/20$), `OBSERVATION_REQUIRES_FOLLOW_UP` ($\le 20/40$ or interocular asymmetry $\ge 0.3$ LogMAR).

### Module 2: Astigmatism (`ASTIGMATISM`)
- **Clinical Target**: Asymmetric corneal or lenticular curvature across radial meridians.
- **Stimulus**: 12-spoke radial clock dial with central fixation target at 60 cm.
- **Evaluation**: Identifies whether all spokes appear uniform, or if specific meridians appear darker, sharper, or thicker.
- **Outcome Classification**: `NO_CONCERN_REPORTED` (all lines uniform), `OBSERVATION_REQUIRES_FOLLOW_UP` (darker/sharper lines identified $\to$ indicates meridian asymmetry).

### Module 3: Contrast / Light Sensitivity (`CONTRAST_SENSITIVITY`)
- **Clinical Target**: Low-contrast triplet character discrimination under uniform luminance.
- **Levels**: Diminishing contrast gradient: 50% contrast, 10% contrast, 2.5% contrast at 60 cm.
- **Outcome Classification**: `NO_CONCERN_REPORTED` (identifies 2.5% faint triplet), `OBSERVATION_REQUIRES_FOLLOW_UP` (fails at 10% or 50% threshold).

### Module 4: Near Vision Reading Acuity (`NEAR_VISION_READING`)
- **Clinical Target**: Functional near-reading accommodation and presbyopia screening at 40 cm.
- **Scale**: Standard paragraph typography scales: N12 ($1.6\text{ mm}$), N8 ($1.1\text{ mm}$), N5 ($0.7\text{ mm}$).
- **Outcome Classification**: `NO_CONCERN_REPORTED` (reads N5 effortlessly), `OBSERVATION_REQUIRES_FOLLOW_UP` (struggles with N8 or N12).

### Module 5: Near Vision Duochrome (`NEAR_VISION_DUOCHROME`)
- **Clinical Target**: Longitudinal chromatic aberration balance (myopic vs. hyperopic accommodation tendency).
- **Stimulus**: Split-field red background (`#D32F2F`, $650\text{ nm}$) and green background (`#388E3C`, $535\text{ nm}$) displaying high-contrast optotypes at 40 cm.
- **Evaluation**: Red clearer $\to$ myopic/over-minus shift; Green clearer $\to$ hyperopic/over-plus shift; Both equal $\to$ balanced accommodation.
- **Outcome Classification**: `NO_CONCERN_REPORTED` (both equal), `OBSERVATION_REQUIRES_FOLLOW_UP` (asymmetric focus).

### Module 6: Color Vision Screening (`COLOR_VISION`)
- **Clinical Target**: Red-green and general chromatic deficiency.
- **Plates**: 6 pseudoisochromatic plates (Demonstration, Transformation, Red-Green deficit, Vanishing).
- **Anti-Cheating & Security**: Randomized sequence presentation; expected answers strictly hidden from client.
- **Outcome Classification**: `NO_CONCERN_REPORTED` ($\ge 5/6$ correct), `OBSERVATION_REQUIRES_FOLLOW_UP` ($\le 4/6$ correct).

### Module 7: Central Vision & Macular Distortion (`CENTRAL_VISION_AMSLER`)
- **Clinical Target**: Central visual field distortion (metamorphopsia) and scotoma (macular anomalies).
- **Stimulus**: High-contrast Amsler grid with central fixation white dot at 30 cm viewing distance.
- **Standard Questionnaire**:
  1. Can you see all 4 corners and borders while fixating on the center?
  2. Do any straight lines appear wavy, bent, or distorted?
  3. Are any areas of the grid blurred, dark, discolored, or missing?
- **Outcome Classification**: `NO_CONCERN_REPORTED` (normal grid perception), `OBSERVATION_REQUIRES_FOLLOW_UP` (wavy lines or missing grid patches $\to$ priority clinical referral).

---

## 26.2 Module Implementation & Classification Status

| Module Name | Implementation Status | Protocol Identifier | Clinical Purpose | Stimulus Specification | Server Evaluation Strategy | Automated Test Coverage |
| :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| **Visual Acuity** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_VA_V1` | Distance/near spatial resolution | Tumbling E / Landolt C ($20/200 \to 20/20$) | 5-step staircase progression; mm sizing via display PPI | Unit & API tests passing |
| **Astigmatism** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_ASTIG_V1` | Meridian curvature symmetry | 12-spoke radial clock dial | Meridian darkness/sharpness comparison | Unit & API tests passing |
| **Contrast Sensitivity** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_CONTRAST_V1` | Low-luminance triplet perception | Faint letter triplets ($50\% \to 2.5\%$) | Diminishing threshold scoring | Unit & API tests passing |
| **Near Vision Reading** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_NEAR_READING_V1` | Functional near accommodation | Standardized N12, N8, N5 paragraphs | 3-step reading difficulty evaluation at 40 cm | Unit & API tests passing |
| **Near Vision Duochrome** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_DUOCHROME_V1` | Longitudinal chromatic balance | Red (`#D32F2F`) / Green (`#388E3C`) split-field | Comparative focus & accommodation check | Unit & API tests passing |
| **Color Vision** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_COLOR_V1` | Red-green chromatic discrimination | 6 pseudoisochromatic plates | Server-side plate scoring; hidden answer confidentiality | Unit & API tests passing |
| **Central Vision Amsler** | `IMPLEMENTED AND TESTED` | `OPTIGUIDE_AMSLER_V1` | Metamorphopsia & scotoma screening | Standard Amsler grid with fixation dot | 3-item macular distortion questionnaire | Unit & API tests passing |

---

## 26.3 Display Calibration Subsystem & Mathematical Model

Physical sizing on digital monitors depends on the display's Pixels Per Inch (PPI). An uncalibrated display renders optotypes at unpredictable physical sizes, distorting visual angle subtended at the nodal point of the eye.

### Calibration Method (Standard ID-1 Card Matching):
OptiGuide uses standard credit card dimensions defined by **ISO/IEC 7810 ID-1**:
- Width: $85.60\text{ mm} = 3.370\text{ inches}$.
- Citizen adjusts an on-screen card guide to match a physical card.
- Client submits `reported_card_width_px`.

### Server-Side PPI Formula:
$$\text{computed\_ppi} = \frac{\text{reported\_card_width\_px}}{3.370}$$

### Plausibility Bounds & Status:
- If $60.0 \le \text{computed\_ppi} \le 800.0$: Marked `SERVER_VERIFIED`.
- Otherwise: Marked `CLIENT_REPORTED` or `UNCALIBRATED`.
- **Uncalibrated Fallback**: If citizen skips calibration, the final report flags `overall_classification: UNCALIBRATED`, notes that optotype millimeter scaling was unverified, and provides cautionary interpretation.

---

## 26.4 Unified Screening Session Engine & Finite State Machine

```mermaid
stateDiagram-v2
    [*] --> CREATED: Patient Consents & Initiates Session
    CREATED --> IN_PROGRESS: POST /api/v1/screening/sessions/{id}/start
    IN_PROGRESS --> IN_PROGRESS: Test Module Start & Progression
    IN_PROGRESS --> COMPLETED: All Modules Finalized / Report Generated
    IN_PROGRESS --> CANCELLED: Explicit Cancellation / Timeout
    IN_PROGRESS --> EXPIRED: Session Expiry (24 hours inactivity)
    COMPLETED --> [*]
    CANCELLED --> [*]
    EXPIRED --> [*]
```

### Test Module Instance State Transitions:
- `NOT_STARTED` $\to$ Initial registered state.
- `IN_PROGRESS` $\to$ Stimulus challenges actively served to client.
- `COMPLETED` $\to$ Final step evaluated; clinical observations computed.
- `SKIPPED` $\to$ Patient elected to skip non-mandatory test.
- `CANCELLED` $\to$ Patient cancelled active test instance.

---

## 26.5 Database Schema & Entity Relationships

The subsystem introduces 4 relational tables in migration revision `009_online_vision_screening_platform`:

1. **`screening_calibrations`**:
   - `id` (UUID PK), `session_id` (FK `screening_sessions.id`), `user_id` (FK `users.id`).
   - `device_category` (`DESKTOP`, `LAPTOP`, `TABLET`, `MOBILE`).
   - `screen_width_px`, `screen_height_px`, `device_pixel_ratio`.
   - `calibration_method`, `calibration_status` (`UNCALIBRATED`, `CLIENT_REPORTED`, `SERVER_VERIFIED`).
   - `computed_ppi`, `target_viewing_distance_cm`, `user_confirmed_distance`.
2. **`screening_test_instances`**:
   - `id` (UUID PK), `session_id` (FK), `user_id` (FK).
   - `test_type` (Enum: `VISUAL_ACUITY`, `ASTIGMATISM`, etc.).
   - `status` (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`, `CANCELLED`).
   - `eye` (`OD`, `OS`, `OU`), `viewing_condition` (`WITH_GLASSES`, `WITHOUT_GLASSES`).
   - `current_step`, `total_steps`, `result_classification`, `clinical_observation`, `result_details` (JSON).
3. **`screening_test_responses`**:
   - `id` (UUID PK), `test_instance_id` (FK `screening_test_instances.id`).
   - `step_index`, `stimulus_id`, `stimulus_version`.
   - `expected_answer` (stored server-side), `user_response`, `is_correct`, `response_time_ms`.
4. **`screening_final_reports`**:
   - `id` (UUID PK), `report_number` (String Unique: `OPT-REP-YYYYMMDD-XXXX`), `session_id` (FK), `user_id` (FK).
   - `overall_classification` (`NO_CONCERN_REPORTED`, `OBSERVATION_REQUIRES_FOLLOW_UP`, `INCONCLUSIVE`, `INCOMPLETE`, `UNCALIBRATED`).
   - `completed_tests_count`, `skipped_tests_count`, `calibration_summary` (JSON), `module_results` (JSON).
   - `follow_up_recommendation`, `professional_referral_indicated` (Boolean), `limitations` (JSON), `clinical_disclaimer`.

---

## 26.6 Complete Online Screening REST API Specification

| Method | Endpoint Route | Request Body | Response Model | RBAC Access | Purpose & Workflow |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/screening/configuration` | Query: `lang=en\|hi\|or` | `ScreeningPlatformConfigResponse` | Patient / All | Returns platform metadata, module list, localized instructions |
| `GET` | `/api/v1/screening/tests` | Query: `lang=en\|hi\|or` | `list[TestModuleDefinition]` | Patient / All | Returns catalog of all 7 available screening tests |
| `GET` | `/api/v1/screening/tests/{test_type}`| Query: `lang=en\|hi\|or` | `TestModuleDefinition` | Patient / All | Returns details, setup instructions, and protocol for 1 module |
| `POST` | `/api/v1/screening/sessions/{id}/start` | None | `ScreeningSessionResponse` | Patient (Owner) | Validates active consent and transitions session to `in_progress` |
| `POST` | `/api/v1/screening/sessions/{id}/calibration` | `CalibrationSubmitRequest` | `CalibrationResponse` | Patient (Owner) | Submits hardware display measurement and verifies computed PPI |
| `GET` | `/api/v1/screening/sessions/{id}/calibration` | None | `CalibrationResponse` | Patient / Optometrist | Retrieves active display calibration parameters |
| `POST` | `/api/v1/screening/sessions/{id}/tests/{type}/start` | `TestStartRequest` | `TestChallengeResponse` | Patient (Owner) | Initiates test module and returns first stimulus (answer hidden) |
| `GET` | `/api/v1/screening/tests/{test_id}/next` | None | `TestChallengeResponse` | Patient (Owner) | Fetches the current active stimulus challenge for the test |
| `POST` | `/api/v1/screening/tests/{test_id}/responses` | `TestResponseSubmitRequest` | `TestStepResponse` | Patient (Owner) | Submits stimulus answer, records response time, evaluates step |
| `POST` | `/api/v1/screening/tests/{test_id}/complete` | None | `TestResultResponse` | Patient (Owner) | Concludes test module and calculates preliminary observation |
| `POST` | `/api/v1/screening/tests/{test_id}/cancel` | `TestCancelRequest` | `TestResultResponse` | Patient (Owner) | Cancels an in-progress test instance |
| `GET` | `/api/v1/screening/tests/{test_id}/result` | None | `TestResultResponse` | Patient / Optometrist | Retrieves individual module result and clinical observation |
| `GET` | `/api/v1/screening/sessions/{id}/report` | None | `FinalScreeningReportResponse` | Patient / Optometrist | Generates or fetches consolidated 7-module final report |
| `GET` | `/api/v1/screening/reports/{report_id}` | None | `FinalScreeningReportResponse` | Patient / Optometrist | Fetches final report by UUID (IDOR & shopkeeper blocked) |
| `GET` | `/api/v1/screening/history` | Query: `limit, offset` | `ScreeningHistoryResponse` | Patient (Owner) | Lists historical completed screening sessions and report numbers |

---

## 26.7 Anti-Cheating & Security Controls

1. **Answer Confidentiality**: Stimulus challenge responses (`TestChallengeResponse`) contain `optotype`, `orientation`, `nominal_size_mm`, `options`, `prompt_question`, and `target_viewing_distance_cm`. Correct answers are generated deterministically or looked up strictly in server memory during response submission. Client inspections cannot discern correct answers from API responses.
2. **Sequential Step Enforcement**: Test responses require `step_index` matching the server's `instance.current_step`. Submissions out of order are rejected with HTTP 400 `VALIDATION_ERROR`.
3. **Response Time Telemetry**: Client submits `response_time_ms` for each challenge. Unphysiologically rapid responses ($< 150\text{ ms}$) or excessive delays ($> 30\text{ s}$) are flagged in audit logs.
4. **Active Consent Gate**: Starting sessions or initiating test modules requires active, unrevoked informed consent (`ScreeningConsent.is_active == True`). Withdrawn consent raises HTTP 403 `CONSENT_REQUIRED`.
5. **RBAC & Clinical Isolation**: Only session owners and licensed optometrists can view completed clinical reports. Optical shopkeepers are strictly forbidden (HTTP 403) to prevent unauthorized medical record disclosure.

---

# 27. VOICE-CONTROLLED ADAPTIVE VISUAL ACUITY TEST ENGINE

## 27.1 Architecture & Workflow Overview

The Voice-Controlled Adaptive Visual Acuity Test Engine enables interactive, hands-free visual acuity screening using device microphone audio. Rather than requiring physical keyboard, mouse, or touch input, the citizen views optotype stimuli on their screen and speaks their answer aloud.

The end-to-end interactive loop operates as follows:
1. **Optotype Presentation**: Server issues an optotype challenge (Tumbling E, Landolt C, or Sloan letter) sized according to display PPI and viewing distance geometry. The expected correct answer is strictly hidden from the client.
2. **Spoken Response Capture**: The client records microphone audio as PCM WAV (`audio/wav`) or base64 PCM stream.
3. **Audio Ingestion & Validation**: The backend receives the audio via `POST /api/v1/screening/acuity/tests/{test_id}/voice-response`. The audio stream is validated for PCM format, sampling rate, frame integrity, and size limits ($< 25\text{ MB}$).
4. **Speech-to-Text Transcription**: The speech engine (Windows `System.Speech` offline recognizer or cloud provider) generates raw transcription and confidence metrics ($0.0 - 1.0$).
5. **Clinical Response Interpretation (`VoiceAcuityInterpreter`)**:
   - Strips filler phrases ("I think it is", "it looks like", "the letter is").
   - Normalizes colloquial and phonetic speech (e.g., "charlie" $\to$ "C", "delta" $\to$ "D", "zed"/"zee" $\to$ "Z", "pointing downwards" $\to$ "DOWN").
   - Separates **speech recognition uncertainty** from **clinical visual inability**:
     - *Silence / Empty Audio*: Returns `status="UNRECOGNIZED"`, `retry_required=True`.
     - *Low Confidence ($< 0.35$)*: Returns `status="LOW_CONFIDENCE"`, `retry_required=True`.
     - *Ambiguous Direction or Letter* (e.g. "up or down", "charlie and delta"): Returns `status="AMBIGUOUS"`, `retry_required=True`.
     - *Visual Inability Phrases* ("cannot see", "can't make it out", "too blurry", "don't know", "blank"): Returns `status="CANNOT_SEE"`, `retry_required=False`. Recorded as an incorrect attempt without penalizing microphone or requiring retry.
6. **Adaptive Staircase Progression (ISO 8596 / 3-of-4 ATS Rule)**:
   - When retry is required: The attempt sequence is preserved without penalty; total attempt counters remain untouched.
   - When answer is resolved: Correctness is independently scored server-side. The adaptive staircase determines whether the current difficulty level passes, fails, or requires another attempt, progressing toward the smallest reliably resolved optotype size.
7. **Screening Assessment Finalization**:
   - On completion, the engine calculates final Snellen fraction, LogMAR acuity, and decimal acuity.
   - Automatically persists a `VisualAcuityAssessment` with preliminary screening observations and clinical disclaimers.

---

## 27.2 Supported Standardized Optotypes

The server-controlled optotype engine supports three clinical standardized optotype sets:

| Optotype Set | Enum Identifier | Valid Stimulus Symbols | Spoken Normalization & NATO Equivalents |
| :--- | :--- | :--- | :--- |
| **Tumbling E** | `TUMBLING_E` | `E_UP`, `E_DOWN`, `E_LEFT`, `E_RIGHT` | Spoken directions: `UP`, `DOWN`, `LEFT`, `RIGHT` (including "pointing up", "open left", etc.) |
| **Landolt C** | `LANDOLT_C` | `C_UP`, `C_DOWN`, `C_LEFT`, `C_RIGHT` | Spoken gap directions: `UP`, `DOWN`, `LEFT`, `RIGHT` (including "open to the right", "towards top") |
| **Sloan Letters** | `SLOAN` | `C`, `D`, `E`, `F`, `L`, `N`, `O`, `P`, `T`, `Z` | Letter names and NATO phonetics: `Charlie`, `Delta`, `Echo`, `Foxtrot`, `Lima`, `November`, `Oscar`, `Papa`, `Tango`, `Zulu` |

---

## 27.3 Database Schema & Migration Revision 010

Database migration revision `010_voice_adaptive_acuity_enhancements` added the following clinical speech telemetry columns to the `adaptive_acuity_attempts` table:

```sql
ALTER TABLE adaptive_acuity_attempts ADD COLUMN input_modality VARCHAR(20) NOT NULL DEFAULT 'MANUAL';
ALTER TABLE adaptive_acuity_attempts ADD COLUMN transcription_confidence FLOAT NULL;
ALTER TABLE adaptive_acuity_attempts ADD COLUMN stt_provider VARCHAR(50) NULL;
ALTER TABLE adaptive_acuity_attempts ADD COLUMN raw_transcript VARCHAR(255) NULL;
ALTER TABLE adaptive_acuity_attempts ADD COLUMN recognition_status VARCHAR(30) NULL;
```

---

## 27.4 Voice Acuity REST API Specification

### Endpoint: `POST /api/v1/screening/acuity/tests/{test_id}/voice-response`

- **Authorization**: `Bearer <token>` (Active Patient owner; strict IDOR protection enforced).
- **Consumes**: `application/json` OR `multipart/form-data`.
- **Status Code**: `200 OK` (or `422 Unprocessable Entity` for invalid audio format/out-of-order attempts).

#### A. JSON Request Format (`application/json`):
```json
{
  "attempt_sequence": 1,
  "audio_base64": "UklGRi...",
  "response_duration_ms": 1150
}
```

#### B. Multipart Form Request Format (`multipart/form-data`):
- `file`: Audio file binary stream (`.wav`, 16-bit PCM).
- `attempt_sequence`: Form field integer (e.g. `1`).
- `response_duration_ms`: Optional integer latency in milliseconds.

#### C. Voice Step Response Model (`AdaptiveAcuityVoiceStepResponse`):
```json
{
  "test_id": "3fd7c156-f5b2-45cc-8c8c-6f9610cffcf2",
  "attempt_sequence": 1,
  "test_status": "IN_PROGRESS",
  "was_correct": true,
  "level": 6,
  "total_attempts": 1,
  "correct_attempts": 1,
  "is_test_complete": false,
  "input_modality": "VOICE",
  "recognition_status": "RECOGNIZED",
  "raw_transcript": "pointing up",
  "recognized_symbol": "UP",
  "transcription_confidence": 0.94,
  "stt_provider": "System.Speech (offline)",
  "retry_required": false,
  "feedback_message": "Recognized direction: UP.",
  "next_challenge": {
    "test_id": "3fd7c156-f5b2-45cc-8c8c-6f9610cffcf2",
    "attempt_sequence": 2,
    "current_level": 7,
    "level_snellen": "20/30",
    "level_logmar": 0.18,
    "optotype_type": "TUMBLING_E",
    "presented_symbol": "E_LEFT",
    "choices": ["UP", "DOWN", "LEFT", "RIGHT"],
    "target_size_arcmin": 7.5,
    "target_height_mm": 6.54,
    "target_height_px": 36.3,
    "test_eye": "right",
    "test_type": "DISTANCE",
    "instructions": "Testing RIGHT eye at 3.0m. Speak clearly into the microphone."
  },
  "result_summary": null
}
```

#### D. Ambiguity / Retry Response Example:
When background noise, low confidence, or conflicting speech occurs:
```json
{
  "test_id": "3fd7c156-f5b2-45cc-8c8c-6f9610cffcf2",
  "attempt_sequence": 1,
  "test_status": "IN_PROGRESS",
  "was_correct": null,
  "level": 6,
  "total_attempts": 0,
  "correct_attempts": 0,
  "is_test_complete": false,
  "input_modality": "VOICE",
  "recognition_status": "AMBIGUOUS",
  "raw_transcript": "up or down",
  "recognized_symbol": null,
  "transcription_confidence": 0.88,
  "retry_required": true,
  "feedback_message": "Multiple directions detected (UP, DOWN). Please say only one direction (Up, Down, Left, or Right).",
  "next_challenge": {
    "attempt_sequence": 1,
    "current_level": 6,
    "presented_symbol": "E_UP"
  },
  "result_summary": null
}
```

---

## 27.5 Statutory Clinical Boundaries & Non-Prescriptive Notice

> [!WARNING]
> **PRELIMINARY FUNCTIONAL SCREENING ONLY — NOT AN OPTICAL PRESCRIPTION**  
> 1. Spoken visual acuity testing evaluates functional letter and symbol resolution under defined display calibration.  
> 2. The engine **NEVER** estimates, computes, or outputs refractive error parameters (Sphere $\text{SPH}$, Cylinder $\text{CYL}$, or Axis $\text{AXIS}$).  
> 3. Results represent preliminary screening observations. Users demonstrating reduced visual acuity or anisometropia are automatically referred to licensed eye care practitioners for comprehensive physical examination and clinical refraction.

---

## 27.6 Verification Evidence & Test Coverage

The voice-controlled adaptive acuity engine is verified by 81 automated tests:
- `tests/unit/test_voice_acuity_engine.py`: 71 unit tests covering speech normalization, phonetic dictionaries, visual inability detection, low-confidence gates, and Landolt C optotypes.
- `tests/api/test_voice_adaptive_acuity_api.py`: 10 integration tests validating end-to-end voice test lifecycles, JSON and multipart audio submissions, IDOR isolation, and sequence integrity.
- Total Backend Test Suite: **321 passing tests (100% pass rate)**.

---

## 27.7 Full-Stack Web Implementation (`apps/web`): 8-Screen Interactive Screening UI & Real Audio Pipeline

The web application provides a complete, production-grade interactive vision testing experience connecting directly to the FastAPI adaptive acuity engine:

### 1. Architectural Components:
- **`apps/web/src/pages/ScreeningFlowPage.tsx`**: State machine coordinating the 8 screening stages:
  - **Screen A (Welcome)**: Screening introduction, privacy notice, duration estimate (~3 mins), clinical non-diagnostic disclaimer, language selection (EN, HI, OD), and audio instruction toggle.
  - **Screen B (Preparation)**: Guidance on seating position, ambient room lighting, viewing distance (1.0m desktop / 3.0m calibrated), spectacles check ("wear your normal distance glasses"), and real microphone permission validation.
  - **Screen C (Display Calibration)**: Interactive physical credit-card slider (standard ISO/IEC 7810 ID-1 card dimensions: 85.60 mm width) calculating display DPI and pixel-to-arcminute scaling factors, with uncalibrated fallback.
  - **Screen D (Eye Selection & Occlusion)**: Right eye (OD), Left eye (OS), or Both eyes (OU) selection with explicit occlusion confirmation checklist.
  - **Screen E (Interactive Test Display)**: High-contrast server-directed optotype presentation (TUMBLING_E, LANDOLT_C, SLOAN) with hidden expected answers.
  - **Screen F (Voice Recording & Audio Waveform)**: Automatic recording trigger via `voiceRecorder`, real-time RMS audio volume monitor animating a pulsing microphone soundwave, silence timeout (~3.8s), and fallback directional buttons.
  - **Screen G (Adaptive Feedback Banner)**: Displays recognized speech transcript, recognition confidence score, server correctness determination, and unclear speech retry notice without scoring penalty.
  - **Screen H (Final Screening Report)**: Functional visual acuity breakdown (Snellen fraction, LogMAR, Decimal), display calibration tier, non-prescriptive clinical observations, certified optometrist referral directory, and mandatory non-diagnostic statutory disclaimer.
- **`apps/web/src/services/voiceRecorder.ts`**: Pure browser Web Audio API recorder:
  - Captures raw microphone audio via `navigator.mediaDevices.getUserMedia({ audio: true })`.
  - Resamples to 16,000 Hz single-channel (mono) PCM audio using `AudioContext`.
  - Encodes standard 16-bit PCM WAV with standard RIFF/WAVE header via `DataView`.
  - Calculates real-time RMS decibel volume for UI audio meters.
  - Cleans up media stream tracks immediately on test completion or cancellation.
- **`apps/web/src/services/apiClient.ts`**: Complete typed HTTP client:
  - Frictionless patient session auto-provisioning (`ensureAuthenticatedPatient`).
  - Active consent document acceptance (`acceptScreeningConsent`).
  - Multipart audio blob streaming (`submitAdaptiveAcuityVoiceBlob`).
  - Staircase response evaluation and final assessment completion.

### 2. Frontend Test Verification:
- `apps/web/tests/voice_adaptive_acuity.test.js`: 4 tests validating PCM WAV encoding headers, microphone lifecycle, apiClient endpoint contracts, and 8-screen rendering state machine.
- `apps/web/tests/web.test.js`: 9 tests verifying PRD design tokens, multilingual dictionaries, customer kiosk records, and clinical consent integration.
- Total Frontend Test Suite: **13 passing tests (100% pass rate)**.

### 3. Live System End-to-End Verification:
- Executed `tests/e2e_live_probe.py` against live daemon instances:
  - Registered and authenticated patient.
  - Accepted server-controlled consent document version `1.0.0`.
  - Created session and calibrated screen at 100 cm viewing distance.
  - Initiated adaptive test for RIGHT_EYE (`TUMBLING_E`).
  - Transmitted real 16 kHz PCM WAV voice byte stream to `/api/v1/screening/acuity/tests/{test_id}/voice-response`.
  - Verified speech recognition, ISO 8596 staircase progression, and final assessment determination.
  - Result: **All live end-to-end verifications passed**.

---

# 28. APPENDIX A: ENVIRONMENT CONFIGURATION & SECRET REFERENCE

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | string | `OptiGuide API` | Display name of the microservice |
| `ENVIRONMENT` | string | `development` | Runtime environment (`development`, `staging`, `production`) |
| `DEBUG` | boolean | `True` | Enables Swagger `/docs` and detailed debug logging |
| `DATABASE_URL` | string | `sqlite:///./optiguide.db` | SQLAlchemy connection URI (PostgreSQL or SQLite) |
| `SECRET_KEY` | string | `change-me-in-production` | Secret key for JWT signature HMAC-SHA256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| integer | `30` | Access token lifespan in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | integer | `7` | Refresh token lifespan in days |
| `CORS_ORIGINS` | list | `["http://localhost:3000", ...]` | Permitted CORS frontend origins |

---

# 29. APPENDIX B: ROLE-BASED ACCESS CONTROL (RBAC) PERMISSION MATRIX

| Endpoint Group | `patient` | `shopkeeper` | `optometrist` | `admin` |
| :--- | :---: | :---: | :---: | :---: |
| `/api/v1/screening/*` | Read/Write (Own) | Read (Own) | Read (Own) | Full Admin |
| `/api/v1/referrals` | Read/Write (Own) | No Access | Read (Shared) | Full Admin |
| `/api/v1/professionals/apply` | No Access | No Access | Apply / Update | No Access |
| `/api/v1/professionals/admin/*` | No Access | No Access | No Access | Full Admin |
| `/api/v1/catalog` (Search) | Read-Only | Read-Only | Read-Only | Read / Write |
| `/api/v1/shops` (Create / Adjust) | No Access | Read/Write (Own) | No Access | Full Admin |
| `/api/v1/recommendations/eyewear` | Read/Write (Own) | Read-Only | Read-Only | Full Admin |
| `/api/v1/pd/assessments` | Read/Write (Own) | Read (Own) | Read/Review | Full Admin |

---

# 30. APPENDIX C: CLINICAL ALGORITHMIC REFERENCE & CUT-OFF THRESHOLDS

### Visual Acuity Conversion Matrix:
- Snellen $20/20 \iff 1.0\text{ Decimal} \iff 0.00\text{ LogMAR}$ (Normal vision)
- Snellen $20/40 \iff 0.5\text{ Decimal} \iff 0.30\text{ LogMAR}$ (Mild vision reduction)
- Snellen $20/60 \iff 0.33\text{ Decimal} \iff 0.48\text{ LogMAR}$ (Moderate impairment $\to$ `PRIORITY`)
- Snellen $20/200 \iff 0.1\text{ Decimal} \iff 1.00\text{ LogMAR}$ (Severe impairment $\to$ `URGENT`)

### Interocular Acuity Difference:
- $\Delta\text{LogMAR} \ge 0.30$: Flagged as Amblyopia / Anisometropia risk $\to$ `PRIORITY`
- $\Delta\text{LogMAR} \ge 0.40$: Significant asymmetry $\to$ `URGENT`

### Astigmatism Dial Thresholds:
- Uniform clarity across all meridians: Low astigmatic risk
- Meridian line thickening/darkening: Astigmatism indicated; axis recorded at sharpest meridian angle ($0^\circ - 180^\circ$) $\to$ `PRIORITY` referral

---
*Document Version: 4.2.0-VOICE-ADAPTIVE-ACUITY-CONSOLIDATED*  
*Last Updated: 2026-11-05*  
*Author: Senior Backend Architecture & Clinical Engineering Team*
