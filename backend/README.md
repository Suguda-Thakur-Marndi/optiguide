# OptiGuide — Backend Service Foundation

High-performance, asynchronous REST API backend for the **OptiGuide** preliminary vision screening and eyewear guidance platform. Built with **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.0**, and **Alembic**.

---

## 1. Backend Architecture

The backend follows a modular, layer-isolated architecture:

```
backend/
├── app/
│   ├── main.py                  # Application factory, CORS, exception handlers, lifecycle
│   ├── api/
│   │   ├── dependencies.py      # Database session and security dependency injection
│   │   └── v1/
│   │       ├── router.py        # Version 1 API router aggregator
│   │       └── health.py        # /health, /health/database, and /health/db endpoints
│   ├── core/
│   │   ├── config.py            # Centralized Pydantic BaseSettings
│   │   ├── logging.py           # Structured logging with credential redaction
│   │   └── exceptions.py        # Core custom exception hierarchy
│   ├── database/
│   │   ├── base.py              # DeclarativeBase for SQLAlchemy models
│   │   ├── session.py           # Engine pooling and live connection pinging
│   │   └── init_db.py           # Schema initialization utility
│   ├── models/                  # Declarative ORM models
│   ├── schemas/
│   │   ├── health.py            # AppInfo, Health, and DatabaseHealth schemas
│   │   ├── common.py            # Generic pagination schemas
│   │   └── error.py             # RFC-compliant error envelope schema
│   ├── repositories/            # Data access abstraction layer
│   ├── services/                # Domain business logic layer
│   ├── middleware/
│   │   ├── error_handler.py     # Global error interceptor
│   │   └── logging_middleware.py# Request execution timing (X-Process-Time-Ms)
│   └── utils/                   # Shared backend utility functions
├── migrations/                  # Alembic migration revisions
├── tests/
│   ├── unit/                    # Configuration, schema, and exception unit tests
│   ├── integration/             # Database session and ping integration tests
│   ├── api/                     # Health and error envelope HTTP tests
│   └── conftest.py              # Pytest fixtures and test client configuration
├── .env.example                 # Environment configuration template
├── alembic.ini                  # Alembic CLI migration configuration
├── pyproject.toml               # Build configuration, Ruff settings, and Pytest configuration
├── requirements.txt             # Pinned backend dependencies
└── README.md
```

---

## 2. Python Prerequisites

- **Python Version:** `>= 3.11` (Tested & verified on `Python 3.12` and `Python 3.13.14`)
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
*(If PowerShell restricts execution scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 3: Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

---

## 4. Database Configuration

### Local Development / Isolated Testing (SQLite)
The default setting uses a zero-dependency local SQLite database:
```env
DATABASE_URL=sqlite:///./local_dev.db
DB_ECHO=false
```

### Production / Staging Deployment (PostgreSQL)
Configure a PostgreSQL connection string utilizing the modern `psycopg` driver:
```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/optiguide_dev
DB_ECHO=false
```

---

## 5. Database Migrations (Alembic)

Run migrations to apply the current schema:
```powershell
alembic upgrade head
```

Generate a new migration when SQLAlchemy models change:
```powershell
alembic revision --autogenerate -m "describe_migration_changes"
```

Rollback the previous migration:
```powershell
alembic downgrade -1
```

---

## 6. Running the FastAPI Application

Start the local development server with auto-reload:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Root Info:** `http://localhost:8000/`
- **Root Health:** `http://localhost:8000/health`
- **System Health:** `http://localhost:8000/api/v1/health`
- **Database Health:** `http://localhost:8000/api/v1/health/database`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`

---

## 7. Automated Testing (Pytest)

Run the full backend test suite:
```powershell
pytest -v
```

Run tests by category:
```powershell
# API endpoint tests
pytest tests/api -v

# Database integration tests
pytest tests/integration -v

# Unit tests
pytest tests/unit -v
```

---

## 8. Code Quality & Linting (Ruff)

Verify formatting and linting:
```powershell
ruff check .
ruff format --check .
```

Automatically apply recommended fixes:
```powershell
ruff check . --fix
ruff format .
```

---

## 9. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **PowerShell script execution error** | Script execution policy | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| **Port 8000 in use** | Process conflict | Set `PORT=8001` in `.env` and start with `--port 8001` |
| **PostgreSQL connection failure** | Service not running | Ensure PostgreSQL is active or switch to `sqlite:///./local_dev.db` |
| **CORS blocked on web/mobile** | Origin not in whitelist | Add client origin (e.g., `http://localhost:8081`) to `CORS_ORIGINS` in `.env` |
