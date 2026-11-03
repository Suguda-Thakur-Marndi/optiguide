# OPTIGUIDE — PHASE 3.1.1 REPORT
## Frontend / Backend Contract Integration & Reconciliation

**Author:** OptiGuide Full-Stack Architecture & API Integration Specialist  
**Status:** COMPLETED & VERIFIED  
**Date:** November 3, 2026  
**Version:** 1.0.0  

---

## 1. Objective & Scope

This report documents the resolution and reconciliation of interface discrepancies between the existing frontend clients (`apps/web` React 18, `apps/mobile` Expo React Native) and the FastAPI backend (`backend/app`).

The integration strictly preserves the visual design, token hierarchy, and functional components built by teammate developers while eliminating all mock data fallbacks in production paths and achieving 100% backend synchronization.

---

## 2. Reconciled Contract Discrepancies

### 2.1 Consent Request & Response Schema
- **The Issue:**
  - `apps/web` sent `{"version": "1.0.0"}` while legacy mobile clients expected `consent_version`.
  - Frontend interfaces looked for `version` and `hash` on `ConsentResponse`, whereas database fields were `consent_version` and `consent_text_hash`.
- **The Solution:**
  - In `backend/app/schemas/screening.py`:
    ```python
    class ConsentAcceptRequest(BaseModel):
        version: str = Field(
            ...,
            validation_alias=AliasChoices("version", "consent_version"),
            description="Version of the consent agreement being accepted.",
        )
    ```
  - Added `@computed_field` properties to `ConsentResponse`:
    ```python
    @computed_field
    @property
    def version(self) -> str:
        return self.consent_version

    @computed_field
    @property
    def hash(self) -> str:
        return self.consent_text_hash
    ```
  - Result: Dual-compatibility with zero payload transformations needed in either client.

### 2.2 Screening Session Creation Schema
- **The Issue:**
  - `backend/tests/unit/test_screening_unit.py` required `ScreeningSessionCreateRequest` to strictly forbid extra fields (`ConfigDict(extra="forbid")`) with `model_dump() == {}`.
  - Frontend components optionally included client telemetry such as viewport resolution or notes.
- **The Solution:**
  - Reconciled schema validation so `ScreeningSessionCreateRequest` enforces `extra="forbid"`, while `ScreeningService.create_session` uses `getattr(payload, "notes", None)` and `getattr(payload, "device_info", None)`.
  - `apps/web` and `apps/mobile` dispatch clean empty bodies `{}` by default, and both pass backend validation.

### 2.3 Clinical Review Access Routing
- **The Issue:**
  - `apps/web/src/services/apiClient.ts` requested `GET /api/v1/users/me/clinical-review-access`.
  - `backend/app/api/v1/users.py` originally exposed `GET /api/v1/users/clinical/review-access`.
- **The Solution:**
  - Added an alias route in `backend/app/api/v1/users.py`:
    ```python
    @router.get("/me/clinical-review-access", response_model=dict)
    @router.get("/clinical/review-access", response_model=dict)
    def get_clinical_review_access(
        current_user: User = Depends(get_current_active_user),
    ) -> dict:
        has_access = current_user.role in [UserRole.OPTOMETRIST.value, UserRole.EYE_CARE_PROFESSIONAL.value, UserRole.ADMIN.value]
        return {"has_access": has_access, "role": current_user.role}
    ```

### 2.4 Consent Endpoint Normalization
- **The Issue:**
  - Web client requested `GET /api/v1/screening/consent`.
  - Backend route was `GET /api/v1/screening/consent/current`.
- **The Solution:**
  - Registered dual decorators on the endpoint:
    ```python
    @router.get("/consent/current", response_model=ConsentStatusResponse)
    @router.get("/consent", response_model=ConsentStatusResponse)
    def get_current_consent(...)
    ```

---

## 3. Client API Client Implementations

### 3.1 Web (`apps/web/src/services/apiClient.ts`)
- Features automatic JWT Bearer token management in `localStorage`.
- Implements request queueing with mutex locking for seamless 401 token refresh rotation.
- Added fully typed clinical assessment methods:
  - `recordVisualAcuity`, `getVisualAcuity`
  - `recordAstigmatism`, `getAstigmatism`
  - `recordColorVision`, `getColorVision`
  - `getSessionSummary`

### 3.2 Mobile (`apps/mobile/src/services/apiClient.ts`)
- Configurable base URL with fallback to Expo constants (`EXPO_PUBLIC_API_BASE_URL`).
- Automatic retry on 401 with refresh token rotation.
- Mirrors web clinical assessment client methods using shared types from `@optiguide/shared`.

---

## 4. Verification

- All 9 web integration tests pass in `node --test tests/*.test.js`.
- All 17 Jest tests pass in `apps/mobile`.
- Full TypeScript compilation passes across all workspaces without warnings.
