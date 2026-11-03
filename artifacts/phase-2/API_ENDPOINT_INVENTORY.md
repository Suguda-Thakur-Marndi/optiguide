# OptiGuide — Phase 2 API Endpoint Inventory

**Platform:** OptiGuide Preliminary Vision Screening and Eyewear Guidance  
**API Prefix:** `/api/v1`  

---

## 1. System & Health Endpoints
- `GET /`: Application identification and runtime status.
- `GET /health`: Lightweight service liveness probe.
- `GET /api/v1/health`: Composite service and database connectivity check.
- `GET /api/v1/health/database`: Live connection check with database type and latency.
- `GET /api/v1/health/db`: Client diagnostic alias.

## 2. Authentication Endpoints (`/api/v1/auth`)
- `POST /api/v1/auth/register`: User registration with Argon2id password hashing (rate-limited: 5/min).
- `POST /api/v1/auth/login`: User login, password verification, and session token generation (rate-limited: 10/min).
- `POST /api/v1/auth/refresh`: Refresh token exchange with automatic rotation and reuse detection.
- `POST /api/v1/auth/logout`: Revoke active refresh token session.
- `POST /api/v1/auth/logout-all`: Revoke all sessions for current authenticated user.
- `GET /api/v1/auth/me`: Retrieve current authenticated user profile.

## 3. User Management Endpoints (`/api/v1/users`)
- `GET /api/v1/users/me`: Retrieve current authenticated user profile.
- `PATCH /api/v1/users/me`: Update profile fields (`full_name`, `phone_number`, `preferred_language`).
- `GET /api/v1/users/me/sessions`: List active and historical sessions for current user.
- `PATCH /api/v1/users/{user_id}/status`: Admin-only endpoint to activate, deactivate, or assign roles.
