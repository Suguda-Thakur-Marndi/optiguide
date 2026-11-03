# OptiGuide — Phase 2.1 Security Audit
## Comprehensive Source-Code Audit, Threat Model & Vulnerability Assessment

**Platform:** OptiGuide Preliminary Vision Screening and Eyewear Guidance  
**Lead:** Principal Backend Architect, Application Security Engineer & QA Automation Lead  
**Date:** November 3, 2026  
**Status:** PASSED (All Remediations Verified with Automated Regressions)  
**Document Path:** `docs/backend/PHASE_2_1_SECURITY_AUDIT.md`  

---

## 1. Executive Summary

This security audit performs an independent, code-level inspection of the OptiGuide Phase 2 Authentication, Authorization, and Session Management subsystem.

While the preliminary Phase 2 report established foundational components (Argon2id hashing, JWT access tokens, and refresh session tracking), this audit uncovered critical vulnerabilities in public registration, rate-limiting spoofability, professional clinical role gating, user enumeration, and concurrent refresh token rotation.

All identified vulnerabilities have been remediated, hardened, and verified through **32 new automated security regression tests**, bringing the total backend suite to **97 passing tests** with 100% clean Ruff linting and formatting.

---

## 2. Security Findings & Severity Classification

| Finding ID | Severity | Category | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-21-01** | **CRITICAL** | Privilege Escalation | Public registration permitted callers to self-assign privileged roles (`admin`, `optometrist`, `shopkeeper`). | **VERIFIED** |
| **SEC-21-02** | **HIGH** | Clinical Safety | Unverified optometrists could access clinical review and prescription review capabilities. | **VERIFIED** |
| **SEC-21-03** | **HIGH** | Rate Limiting Bypass | Untrusted `X-Forwarded-For` header spoofing allowed trivial rate-limit circumvention. | **VERIFIED** |
| **SEC-21-04** | **HIGH** | Concurrency / Race | Non-atomic refresh token rotation permitted race collisions and accidental valid session invalidation. | **VERIFIED** |
| **SEC-21-05** | **MEDIUM** | Information Disclosure | Account status leakage and timing discrepancies in login allowed email enumeration. | **VERIFIED** |
| **SEC-21-06** | **MEDIUM** | Denial of Service | Unbounded password input length allowed CPU starvation attacks via Argon2id. | **VERIFIED** |
| **SEC-21-07** | **MEDIUM** | Cryptographic Token | Missing strict UUID validation and required claims (`iss`, `aud`, `iat`) in JWT decoder. | **VERIFIED** |
| **SEC-21-08** | **LOW** | Schema Integrity | User profile update (`PATCH /me`) lacked strict field forbidding, permitting ignored extra payload injection. | **VERIFIED** |
| **SEC-21-09** | **LOW** | Role Vocabulary | Discrepancy between canonical role vocabulary (`USER`, `SHOPKEEPER`, `EYE_CARE_PROFESSIONAL`, `ADMIN`) and implementation. | **VERIFIED** |

---

## 3. Deep-Dive Security Finding Analysis

### Finding SEC-21-01: Public Self-Registration with Privileged Roles
- **Severity:** **CRITICAL**
- **Affected Files:** `backend/app/schemas/auth.py`, `backend/app/services/auth_service.py`
- **Vulnerability Details:** `UserRegisterRequest` declared `role: UserRole = Field(default=UserRole.PATIENT)`, and `AuthService.register` assigned `role=payload.role.value`. Any malicious client submitting `POST /api/v1/auth/register` with `{"role": "admin"}` or `{"role": "optometrist"}` received full administrative or clinical privileges immediately.
- **Risk:** Complete system compromise, unauthorized database access, unverified clinical approvals.
- **Remediation:**
  1. Added explicit Pydantic field validator on `UserRegisterRequest.role` that rejects any privileged role (`admin`, `optometrist`, `eye_care_professional`, `shopkeeper`) with HTTP 422.
  2. Configured `extra="forbid"` on `UserRegisterRequest` to block unmapped administrative attributes (e.g. `is_admin`, `is_verified`).
  3. In `AuthService.register`, unconditionally enforced default role `UserRole.PATIENT.value`.
- **Regression Tests:** `backend/tests/api/test_phase2_1_security_hardening.py::test_public_registration_blocks_privileged_roles[*]`, `test_public_registration_blocks_injected_admin_fields`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-02: Unverified Clinical Professional Access
- **Severity:** **HIGH**
- **Affected Files:** `backend/app/api/dependencies.py`, `backend/app/api/v1/users.py`
- **Vulnerability Details:** The existing clinician dependency `require_clinician` verified only that `current_user.role in ("optometrist", "admin")`. It did not check `current_user.is_verified`. Consequently, unvetted individuals claiming to be optometrists could access clinical review capabilities.
- **Risk:** Violation of healthcare screening boundaries and safety regulations.
- **Remediation:**
  1. Introduced `require_verified_professional` dependency requiring `role in (OPTOMETRIST, EYE_CARE_PROFESSIONAL, ADMIN)`.
  2. For non-admin accounts, explicitly enforced `current_user.is_verified == True`. Unverified professionals receive HTTP 403 Forbidden with `"Professional account requires verification by an authorized administrator."`
  3. Mounted `GET /api/v1/users/clinical/review-access` to gate future clinical review features.
- **Regression Tests:** `backend/tests/api/test_phase2_1_security_hardening.py::test_role_authorization_matrix` (Tests B, C, D)
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-03: Rate Limiting Bypass via `X-Forwarded-For` Header Spoofing
- **Severity:** **HIGH**
- **Affected Files:** `backend/app/api/dependencies.py`, `backend/app/core/config.py`
- **Vulnerability Details:** `get_client_ip` blindly parsed `request.headers.get("X-Forwarded-For")`. An attacker could rotate fake IP addresses in the `X-Forwarded-For` header on each request, completely bypassing the sliding-window rate limiters on `/register` and `/login`.
- **Risk:** Brute-force credential stuffing, password guessing, automated account creation spam.
- **Remediation:**
  1. Added `TRUST_FORWARDED_FOR: bool = False` and `TRUSTED_PROXIES: list[str] = ["127.0.0.1", "::1"]` to application settings.
  2. In `get_client_ip`, `X-Forwarded-For` is strictly ignored unless `TRUST_FORWARDED_FOR` is explicitly enabled AND the immediate TCP connection host belongs to `TRUSTED_PROXIES`.
  3. Structured `BaseRateLimiter` and `InMemoryRateLimiter` interfaces to facilitate future Redis clustering.
- **Regression Tests:** `backend/tests/unit/test_phase2_1_security_unit.py::test_client_ip_anti_spoofing`, `backend/tests/api/test_phase2_1_security_hardening.py::test_rate_limiter_anti_spoofing_resistance`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-04: Refresh Token Rotation Concurrency Race Condition
- **Severity:** **HIGH**
- **Affected Files:** `backend/app/repositories/session_repo.py`, `backend/app/services/auth_service.py`
- **Vulnerability Details:** Refresh token rotation performed non-atomic `get_by_token_hash`, verified `if not session.is_revoked`, and then separately revoked and created new sessions. Two concurrent requests presenting the same token could both read `is_revoked == False` and both rotate the session, OR the second request could trigger full account invalidation and terminate valid sessions due to network jitter.
- **Risk:** Session desynchronization, double-rotation, denial of service for legitimate mobile users under concurrent refresh requests.
- **Remediation:**
  1. Added `SessionRepository.rotate_session_atomic` executing conditional SQL updates: `UPDATE user_sessions SET is_revoked = true, revoked_at = :now WHERE id = :session_id AND is_revoked = false`.
  2. If the atomic update returns `False`, the system recognizes an in-flight concurrent duplicate and safely raises `TokenRevokedException` without nuking the account's active sessions.
  3. Added `.with_for_update()` row locking support on PostgreSQL connections in `SessionRepository.get_by_token_hash`.
  4. Preserved strict reuse detection: Sequential requests presenting already-revoked tokens trigger `revoke_all_for_user`.
- **Regression Tests:** `backend/tests/api/test_auth_api.py::test_refresh_token_lifecycle_and_reuse_detection`, `backend/tests/integration/test_auth_integration.py::test_token_rotation_integration`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-05: Account Status Disclosure and Timing Discrepancies on Login
- **Severity:** **MEDIUM**
- **Affected Files:** `backend/app/services/auth_service.py`, `backend/app/core/security.py`
- **Vulnerability Details:**
  1. `AuthService.login` checked `if not user.is_active` BEFORE verifying the password. Probing deactivated emails with random passwords revealed account existence via HTTP 403 vs 401.
  2. If a queried user did not exist, `login` returned immediately (< 1ms), whereas an existing user incurred a 25ms Argon2id hash verification, exposing a side-channel timing discrepancy for email enumeration.
- **Risk:** User enumeration, employee reconnaissance, targeted credential stuffing.
- **Remediation:**
  1. If `user is None`, `AuthService.login` executes `verify_password(payload.password, DUMMY_ARGON2_HASH)` before raising HTTP 401 `AuthenticationException("Invalid email or password.")`.
  2. Password verification is performed FIRST. Only after credentials match is `is_active` verified.
- **Regression Tests:** `backend/tests/api/test_phase2_1_security_hardening.py::test_login_error_consistency_prevents_user_enumeration`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-06: Denial of Service via Unbounded Password Length
- **Severity:** **MEDIUM**
- **Affected Files:** `backend/app/schemas/auth.py`, `backend/app/core/security.py`
- **Vulnerability Details:** Password inputs lacked an upper length constraint. A malicious client could send megabyte-sized password strings causing extreme CPU exhaustion during Argon2id memory-hard hashing.
- **Risk:** Compute starvation and Denial of Service against backend worker processes.
- **Remediation:**
  1. Added `max_length=128` to `UserRegisterRequest.password` and `UserLoginRequest.password`.
  2. Enforced maximum length validation (128 characters) in `validate_password_strength`.
- **Regression Tests:** `backend/tests/unit/test_phase2_1_security_unit.py::test_password_boundary_validation`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-07: Incomplete JWT Claim & Subject Validation
- **Severity:** **MEDIUM**
- **Affected Files:** `backend/app/core/security.py`
- **Vulnerability Details:** `decode_access_token` did not enforce UUID syntax validation on `sub`, nor did it require standard claims `iss`, `aud`, `iat` in `options={"require": [...]}`.
- **Risk:** Token substitution or forged claim injection.
- **Remediation:**
  1. Enforced strict UUID parsing on `sub` in `decode_access_token`.
  2. Enforced required claims: `["sub", "exp", "type", "role", "iss", "aud", "iat"]`.
  3. Enforced explicit algorithm whitelist `algorithms=[settings.JWT_ALGORITHM]`.
- **Regression Tests:** `backend/tests/unit/test_phase2_1_security_unit.py::test_jwt_strict_uuid_validation`, `test_jwt_algorithm_none_rejection`, `test_jwt_missing_required_claims`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-08: Privilege Injection in User Profile Updates
- **Severity:** **LOW**
- **Affected Files:** `backend/app/schemas/auth.py`
- **Vulnerability Details:** `UserUpdateRequest` lacked `model_config = ConfigDict(extra="forbid")`. Clients attempting to send `{"role": "admin", "is_verified": true}` did not trigger explicit schema rejections.
- **Risk:** Hidden field acceptance, ambiguity in security boundary enforcement.
- **Remediation:**
  1. Configured `model_config = ConfigDict(extra="forbid")` on `UserUpdateRequest` and `UserRegisterRequest`.
  2. Attempts to supply unapproved fields return HTTP 422 Unprocessable Content.
- **Regression Tests:** `backend/tests/api/test_phase2_1_security_hardening.py::test_user_profile_update_forbids_privileged_fields[*]`
- **Verification Result:** **VERIFIED**

---

### Finding SEC-21-09: Role Vocabulary Discrepancy & Aliasing
- **Severity:** **LOW**
- **Affected Files:** `backend/app/schemas/auth.py`, `backend/app/models/user.py`, `shared/types/user.ts`
- **Vulnerability Details:** The platform specification uses `USER`, `SHOPKEEPER`, `EYE_CARE_PROFESSIONAL`, `ADMIN`, while the implementation used `patient` and `optometrist`.
- **Risk:** Type fragmentation between frontend client models and backend storage.
- **Remediation:**
  1. Formalized `UserRole` enum with canonical roles (`USER`, `SHOPKEEPER`, `EYE_CARE_PROFESSIONAL`, `ADMIN`) and backward-compatible aliases (`PATIENT`, `OPTOMETRIST`).
  2. Added bidirectional alias normalization in `UserRole.normalize_role`.
  3. Updated `shared/types/user.ts` to include canonical roles and wire-format response types.
- **Regression Tests:** `backend/tests/unit/test_phase2_1_security_unit.py::test_role_enum_canonicalization`
- **Verification Result:** **VERIFIED**
