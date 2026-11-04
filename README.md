# OptiGuide — Preliminary Vision Screening & Eyewear Guidance Platform

> [!IMPORTANT]
> **Clinical Safety Notice:** OptiGuide is strictly a preliminary vision screening and eyewear guidance platform. It is not a diagnostic system and must not independently prescribe lens power or clinical treatments. All findings require professional evaluation by qualified optometrists or ophthalmologists.

---

## Master Documentation

All project architecture, API specifications, clinical workflows, data models, Alembic migrations, security standards, and phase completion reports have been consolidated into **one master document**:

👉 **[OptiGuide Backend Master Documentation](docs/OPTIGUIDE_BACKEND_MASTER.md)**

---

## Quick Start (Backend)

### 1. Environment Setup & Dependencies
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database Migrations
```powershell
python -m alembic upgrade head
```

### 3. Run FastAPI Application
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at: `http://localhost:8000/docs`.

### 4. Run Automated Test Suite
```powershell
python -m pytest tests -v
```

---

## Repository Structure
- `backend/`: FastAPI application, SQLAlchemy models, Pydantic schemas, Alembic migrations, and automated test suite.
- `apps/web/`: Web application interface.
- `apps/mobile/`: Cross-platform mobile client application.
- `docs/OPTIGUIDE_BACKEND_MASTER.md`: Master documentation and single source of truth.
