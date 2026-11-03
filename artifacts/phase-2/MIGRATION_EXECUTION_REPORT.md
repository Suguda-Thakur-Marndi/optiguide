# OptiGuide — Phase 2 Migration Execution Report

**Date:** November 3, 2026  
**Migration Engine:** Alembic 1.20.1  
**Database Engines Tested:** PostgreSQL (schema validation) & SQLite (local execution)  

---

## 1. Migration Revisions Applied
1. `001_initial_baseline.py` (Phase 1 Baseline Anchor)
2. `002_user_and_auth.py` (Phase 2 Users and UserSessions Tables)

## 2. Upgrade / Downgrade Verification Execution
```powershell
Set-Location backend; alembic upgrade head; alembic downgrade -1; alembic upgrade head; Set-Location ..
```

Output:
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Running upgrade 001_initial_baseline -> 002_user_and_auth, Add users and user_sessions tables for authentication
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Running downgrade 002_user_and_auth -> 001_initial_baseline, Add users and user_sessions tables for authentication
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Running upgrade 001_initial_baseline -> 002_user_and_auth, Add users and user_sessions tables for authentication
```

## 3. Verified Schema Elements
- `users` table created with columns `id`, `email`, `hashed_password`, `full_name`, `role`, `phone_number`, `preferred_language`, `is_active`, `is_verified`, `created_at`, `updated_at`, `last_login_at`.
- Unique index on `users.email`.
- `user_sessions` table created with columns `id`, `user_id`, `session_token_hash`, `user_agent`, `ip_address`, `is_revoked`, `expires_at`, `created_at`, `revoked_at`.
- Foreign key `user_sessions.user_id` referencing `users.id` with `ON DELETE CASCADE`.
- Unique index on `user_sessions.session_token_hash`.
- Reversible downgrade drops all indexes and tables cleanly.
