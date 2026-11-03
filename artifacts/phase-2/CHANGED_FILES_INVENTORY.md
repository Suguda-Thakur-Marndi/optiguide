# OptiGuide — Phase 2 Changed Files Inventory

**Phase:** Phase 2 (Authentication, Authorization & User Management)  
**Date:** November 3, 2026  

---

## 1. Created Files
| Path | Description |
|---|---|
| `backend/app/models/user.py` | Declarative SQLAlchemy User entity |
| `backend/app/models/session.py` | Declarative SQLAlchemy UserSession entity |
| `backend/app/core/security.py` | Argon2id hashing, JWT creation/decoding, token hashing |
| `backend/app/schemas/auth.py` | Pydantic v2 schemas for registration, login, profile, and sessions |
| `backend/app/repositories/user_repo.py` | User data access repository |
| `backend/app/repositories/session_repo.py` | UserSession data access repository |
| `backend/app/services/auth_service.py` | Authentication domain logic service |
| `backend/app/services/user_service.py` | User profile domain logic service |
| `backend/app/api/v1/auth.py` | `/api/v1/auth/` endpoint routes |
| `backend/app/api/v1/users.py` | `/api/v1/users/` endpoint routes |
| `backend/migrations/versions/002_user_and_auth.py` | Alembic migration for users and user_sessions |
| `backend/tests/unit/test_security_auth.py` | Unit tests for Argon2id, JWT, and rate limiting |
| `backend/tests/api/test_auth_api.py` | API tests for registration, login, refresh, logout |
| `backend/tests/api/test_users_api.py` | API tests for profile and session endpoints |
| `backend/tests/integration/test_auth_integration.py` | Integration tests for database persistence and rotation |
| `docs/backend/PHASE_2_PRE_IMPLEMENTATION_AUDIT.md` | Pre-implementation architectural audit |
| `docs/backend/PHASE_2_AUTHENTICATION_DESIGN.md` | Architecture design specification |
| `docs/backend/PHASE_2_SECURITY_AUDIT.md` | Comprehensive security review |
| `docs/backend/PHASE_2_COMPLETION_REPORT.md` | Phase 2 completion artifact |
| `docs/phase-reports/PHASE_2_REPORT.md` | Phase report |

## 2. Modified Files
| Path | Modification Summary |
|---|---|
| `backend/pyproject.toml` | Added `argon2-cffi`, `pyjwt`, `email-validator` |
| `backend/requirements.txt` | Pinned auth dependencies |
| `backend/README.md` | Updated architecture, endpoint inventory, and security parameters |
| `backend/.env.example` | Added JWT, password, and rate-limiting environment variables |
| `backend/app/core/config.py` | Added settings fields and production secret validator |
| `backend/app/core/exceptions.py` | Added auth exception hierarchy (`AuthenticationException`, etc.) |
| `backend/app/middleware/error_handler.py` | Added `optiguide_exception_handler` mapping to RFC envelopes |
| `backend/app/main.py` | Registered `OptiGuideException` and mounted `/auth` and `/users` |
| `backend/app/models/__init__.py` | Exported `User` and `UserSession` |
| `backend/app/api/dependencies.py` | Added `get_current_user`, `require_roles`, `rate_limit` |
| `backend/app/api/v1/router.py` | Included auth and users routers |
| `backend/tests/conftest.py` | Added rate limiter state cleanup between tests |
| `backend/tests/unit/test_security_auth.py` | Added rate limiter unit test |
