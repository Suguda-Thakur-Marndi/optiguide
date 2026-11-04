# OptiGuide — Backend Service Foundation

> [!TIP]
> **Complete Master Documentation:** For the unified single source of truth across all 4 project phases, see **[OptiGuide Backend Master Documentation](../docs/OPTIGUIDE_BACKEND_MASTER.md)**.

High-performance, asynchronous REST API backend for the **OptiGuide** preliminary vision screening and eyewear guidance platform. Built with **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.0**, and **Alembic**.

---

## 1. Backend Architecture

The backend follows a modular, layer-isolated architecture:

```
backend/
├── app/
│   ├── main.py                  # Application factory, CORS, exception handlers, lifecycle
│   ├── api/
│   │   ├── dependencies.py      # Database session, get_current_user, RBAC, rate-limiting
│   │   └── v1/
│   │       ├── router.py        # Version 1 API router aggregator
│   │       ├── health.py        # /health, /health/database, and /health/db endpoints
│   │       ├── auth.py          # /auth/register, /login, /refresh, /logout, /me
│   │       └── users.py         # /users/me, /users/me/sessions, /users/{id}/status
│   ├── core/
│   │   ├── config.py            # Centralized Pydantic BaseSettings & JWT configuration
│   │   ├── logging.py           # Structured logging with SanitizingFilter and credential masking
│   │   ├── exceptions.py        # Core custom exception hierarchy
│   │   └── security.py          # Argon2id password hashing and JWT access token engine
│   ├── database/
│   │   ├── base.py              # DeclarativeBase for SQLAlchemy models
│   │   ├── session.py           # Engine pooling, get_db dependency, connection ping
│   │   └── init_db.py           # Schema initialization utility (local dev / test only)
│   ├── models/                  # Declarative ORM models
│   │   ├── user.py              # User entity (UUID, email, password hash, role)
│   │   └── session.py           # UserSession entity (refresh token hash, rotation state)
│   ├── schemas/
│   │   ├── auth.py              # UserRegister, UserLogin, AuthResponse, UserProfileResponse
│   │   ├── health.py            # AppInfo, Health, and DatabaseHealth schemas
│   │   ├── common.py            # Generic pagination schemas (PEP 695)
│   │   └── error.py             # RFC-compliant error envelope schema
│   ├── repositories/            # Data access abstraction layer
│   │   ├── user_repo.py         # User entity queries and updates
│   │   └── session_repo.py      # Refresh session queries, rotation, and revocation
│   ├── services/                # Domain business logic layer
│   │   ├── auth_service.py      # Registration, authentication, token rotation, logout
│   │   └── user_service.py      # Profile management and session inspection
│   ├── middleware/
│   │   ├── error_handler.py     # Global error interceptor (RFC envelopes)
│   │   └── logging_middleware.py# Request execution timing (X-Process-Time-Ms)
│   └── utils/                   # Shared backend utility functions
├── migrations/                  # Alembic migration revisions
│   ├── versions/
│   │   ├── 001_initial_baseline.py  # Phase 1 baseline migration anchor
│   │   └── 002_user_and_auth.py     # Phase 2 users and user_sessions tables
│   └── env.py                   # Migration environment with dual sys.path
├── tests/
│   ├── unit/                    # Configuration, schema, exception, security unit tests
│   ├── integration/             # Database session, auth persistence, and ping integration tests
│   ├── api/                     # Health, auth, user, and error envelope HTTP tests
│   └── conftest.py              # Pytest fixtures and isolated test client configuration
├── .env.example                 # Environment configuration template
├── alembic.ini                  # Alembic CLI migration configuration
├── pyproject.toml               # Build configuration, Ruff settings, and Pytest configuration
├── requirements.txt             # Pinned backend dependencies
└── README.md
```

---

## 2. Python Prerequisites

- **Python Version:** `>= 3.12` (Tested & verified on `Python 3.12` and `Python 3.13.14`)
- **Package Manager:** `pip`
- **Operating System:** Windows 10/11 (PowerShell), macOS, or Linux

---

## 3. Local Development Setup (Windows PowerShell)

### Step 1: Create Virtual Environment
From the `backend/` directory:
```powershell
python -m venv .venv
```

### Step 2: Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy template and configure local settings:
```powershell
Copy-Item .env.example .env
```

### Step 5: Run Database Migrations
```powershell
alembic upgrade head
```

### Step 6: Start FastAPI Development Server
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
API endpoints will be accessible at:
- **Root Info:** `http://localhost:8000/`
- **API Liveness:** `http://localhost:8000/health`
- **API v1 Diagnostics:** `http://localhost:8000/api/v1/health`
- **Interactive Swagger Docs (when `APP_DEBUG=true`):** `http://localhost:8000/docs`

---

## 4. Authentication & Authorization Architecture

### 4.1 Password Security (Argon2id)
Passwords are encrypted using Argon2id via `argon2-cffi` configured with OWASP-recommended parameters:
- **Memory Cost:** 64 MB ($65,536$ KiB)
- **Time Cost:** 3 passes
- **Parallelism:** 4 threads
- **Minimum Length:** 8 characters, requiring at least one letter and one number.

### 4.2 Token Management
- **Access Tokens:** Short-lived JWTs (15 minutes default) signed with `HS256`. Carries `sub`, `email`, `role`, and `type="access"` claims.
- **Refresh Tokens:** High-entropy base64 strings (256 bits). Only SHA-256 hashes are persisted in the database (`user_sessions` table).
- **Token Rotation:** Every `/refresh` operation revokes the current session and issues a new token pair.
- **Reuse Detection:** If an already-rotated or revoked refresh token is presented, the system triggers a security alert and immediately terminates all active sessions for that user account.

### 4.3 Role-Based Access Control (RBAC)
Supported user roles:
- `patient`: Vision screening taker, eyewear recommendation recipient.
- `optometrist`: Clinician reviewing preliminary screenings and prescriptions.
- `shopkeeper`: Retail staff matching physical frames.
- `admin`: System administrator for user status and maintenance.

---

## 5. API Endpoint Inventory

### 5.1 Health & Diagnostics
- `GET /`: Application identification and runtime status.
- `GET /health`: Fast service liveness probe.
- `GET /api/v1/health`: Composite system and database readiness check.
- `GET /api/v1/health/database`: Live database ping with latency measurement.
- `GET /api/v1/health/db`: Mobile/web diagnostic screen alias.

### 5.2 Authentication Endpoints (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Create new user account (rate-limited: 5/min).
- `POST /api/v1/auth/login`: Authenticate credentials and receive token pair (rate-limited: 10/min).
- `POST /api/v1/auth/refresh`: Rotate refresh token and obtain new access token.
- `POST /api/v1/auth/logout`: Revoke active refresh session.
- `POST /api/v1/auth/logout-all`: Revoke all sessions for current authenticated user.
- `GET /api/v1/auth/me`: Retrieve current authenticated user profile.

### 5.3 User Profile Endpoints (`/api/v1/users`)
- `GET /api/v1/users/me`: Retrieve current user profile.
- `PATCH /api/v1/users/me`: Update editable profile fields (`full_name`, `phone_number`, `preferred_language`).
- `GET /api/v1/users/me/sessions`: List active and historical sessions for current user.
- `PATCH /api/v1/users/{user_id}/status`: Admin-only endpoint to activate, deactivate, or assign roles.

---

## 6. Testing & Quality Assurance

### Run Test Suite
```powershell
python -m pytest backend/tests -v
```

### Run Linter & Formatter
```powershell
ruff check backend
ruff format --check backend
```
