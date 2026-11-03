# OptiGuide — Phase 2 Dependency Changes

**Phase:** Phase 2 (Authentication, Authorization & User Management)  
**Date:** November 3, 2026  

---

## 1. Added Production Dependencies
| Package | Version Constraint | Purpose |
|---|---|---|
| `argon2-cffi` | `>=23.1.0,<26.0.0` | OWASP-recommended Argon2id password hashing and verification |
| `pyjwt` | `>=2.8.0,<3.0.0` | RFC 7519 compliant JSON Web Token (JWT) encoding and verification |
| `email-validator` | `>=2.1.0,<3.0.0` | RFC-compliant email address validation for Pydantic `EmailStr` |

## 2. Updated Configuration Files
- `backend/pyproject.toml`
- `backend/requirements.txt`
