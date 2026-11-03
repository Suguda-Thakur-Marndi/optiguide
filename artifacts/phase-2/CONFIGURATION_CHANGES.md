# OptiGuide — Phase 2 Configuration Changes

**Phase:** Phase 2 (Authentication, Authorization & User Management)  
**Date:** November 3, 2026  

---

## 1. Added Settings in `backend/app/core/config.py`
| Setting | Type | Default Value | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | `str` | `dev-insecure-secret-key-change-in-production-optiguide-2026` | Symmetric key for signing JWT tokens |
| `JWT_ALGORITHM` | `str` | `HS256` | Algorithm for JWT signature verification |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | Access token lifespan in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `int` | `7` | Refresh token lifespan in days |
| `JWT_ISSUER` | `str` | `optiguide-api` | JWT `iss` claim value |
| `JWT_AUDIENCE` | `str` | `optiguide-client` | JWT `aud` claim value |
| `PASSWORD_MIN_LENGTH` | `int` | `8` | Minimum password length |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | `int` | `10` | Maximum login attempts per minute per IP |
| `REGISTER_RATE_LIMIT_PER_MINUTE` | `int` | `5` | Maximum registration attempts per minute per IP |

## 2. Production Security Validation
A model validator in `Settings` enforces that in `production` environment (`APP_ENV=production`), `JWT_SECRET_KEY` cannot match default values and must be at least 32 characters long.
