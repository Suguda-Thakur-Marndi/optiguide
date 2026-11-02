# OptiGuide Backend — Security Baseline & Controls

## 1. Security Overview

OptiGuide's backend service processes preliminary optical screenings and referral recommendations. This document defines the security controls implemented in Phase 1 and outlines future security requirements for clinical production readiness.

---

## 2. Controls Implemented in Phase 1

### 2.1. Environment-Based Secrets & Zero Hardcoded Credentials
- **Implementation:** Centralized via Pydantic Settings (`app/core/config.py`).
- **Policy:** No database passwords, secret keys, or environment-specific connection strings are committed to version control.
- **Enforcement:** `.gitignore` excludes all `.env` files, `.venv`, SQLite `.db` files, and local caches.

### 2.2. Strict CORS Configuration
- **Implementation:** `CORSMiddleware` configured in `app/main.py`.
- **Policy:** Explicit origins parsed from `CORS_ORIGINS`. Wildcards (`"*"`) with credential sharing are prevented.

### 2.3. Safe Error Handling & Traceback Sanitization
- **Implementation:** Global exception handlers in `app/middleware/error_handler.py`.
- **Policy:** Unhandled server exceptions (HTTP 500) return sanitized client messages. Raw SQL queries, database credentials, and file system tracebacks are never transmitted to clients.

### 2.4. Credential Redaction in Logging
- **Implementation:** Filter in `app/core/logging.py`.
- **Policy:** Header keys such as `authorization`, `cookie`, `password`, and `token` are automatically masked to `[REDACTED]` prior to logging.

### 2.5. Parameterized Queries & ORM Protection
- **Implementation:** SQLAlchemy 2.0 ORM and parameterized queries.
- **Policy:** No raw dynamic SQL concatenation, eliminating SQL injection vectors.

---

## 3. Security Roadmap for Subsequent Phases

| Security Domain | Phase 1 Status | Planned Phase 2+ Implementation |
| :--- | :--- | :--- |
| **Authentication** | Unauthenticated (Health/Diag) | JWT (OAuth2 Password Bearer) with Argon2/bcrypt password hashing |
| **Authorization** | Open foundation | Role-Based Access Control (Patient, Optometrist, Shopkeeper, Admin) |
| **Rate Limiting** | None | SlowAPI / Redis-backed rate limiting on sensitive routes |
| **Data Encryption** | In-transit (HTTPS) | Column-level encryption for sensitive clinical screening parameters |
| **Audit Logging** | Request timing logged | Immutable audit trail for clinical record access |
