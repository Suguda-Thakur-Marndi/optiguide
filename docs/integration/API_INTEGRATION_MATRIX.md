# OptiGuide — API Integration Matrix

**Document:** `docs/integration/API_INTEGRATION_MATRIX.md`  
**Status:** COMPLETE & VERIFIED  
**Date:** November 3, 2026  

---

## 1. Matrix Overview

This matrix maps every frontend screen, user action, form, and button across both the Universal Expo client (`apps/mobile`) and the React + Vite web client (`apps/web`) to their corresponding FastAPI backend endpoints.

---

## 2. Comprehensive Integration Matrix

| Frontend Page / Component | User Action | UI Element | HTTP Method | Backend Endpoint | Request Payload | Response Model | Auth Required | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **System Diagnostics** (`DiagnosticsScreen.tsx` / Web Health Tab) | Check API Liveness | "Test Connection" button | `GET` | `/api/v1/health` | None | `HealthResponse` | No | **VERIFIED** |
| **System Diagnostics** (`DiagnosticsScreen.tsx` / Web Health Tab) | Check DB Connectivity | "Test Connection" button | `GET` | `/api/v1/health/db` | None | `DatabaseHealthResponse` | No | **VERIFIED** |
| **Authentication** (`login.tsx` / Web Auth Tab) | Register Patient | "Create Account" submit | `POST` | `/api/v1/auth/register` | `{"email", "password", "full_name"}` | `AuthResponse` (`access_token`, `refresh_token`, `user`) | No | **VERIFIED** |
| **Authentication** (`login.tsx` / Web Auth Tab) | Sign In | "Sign In" submit | `POST` | `/api/v1/auth/login` | `{"email", "password"}` | `AuthResponse` (`access_token`, `refresh_token`, `user`) | No | **VERIFIED** |
| **Authentication** (`apiClient.ts` interceptor) | Rotate Token | Auto-intercept on 401 | `POST` | `/api/v1/auth/refresh` | `{"refresh_token"}` | `TokenRefreshResponse` | No | **VERIFIED** |
| **Authentication** (`profile/index.tsx` / Web Nav) | Sign Out Active Session | "Sign Out" button | `POST` | `/api/v1/auth/logout` | `{"refresh_token"}` | `MessageResponse` | No | **VERIFIED** |
| **Authentication** (`profile/index.tsx` / Web Nav) | Revoke All Sessions | "Sign Out Everywhere" button | `POST` | `/api/v1/auth/logout-all` | None | `MessageResponse` | Yes (Bearer) | **VERIFIED** |
| **User Profile** (`profile/index.tsx` / Web Auth Tab) | View My Profile | Page Mount / Tab Load | `GET` | `/api/v1/users/me` | None | `UserProfileResponse` | Yes (Bearer) | **VERIFIED** |
| **User Profile** (`profile/index.tsx` / Web Profile) | Update Profile Details | "Save Changes" button | `PATCH` | `/api/v1/users/me` | `{"full_name", "phone_number", "preferred_language"}` | `UserProfileResponse` | Yes (Bearer) | **VERIFIED** |
| **User Profile** (`profile/index.tsx` / Web Profile) | View Active Sessions | Page Mount / Tab Load | `GET` | `/api/v1/users/me/sessions` | None | `list[SessionResponse]` | Yes (Bearer) | **VERIFIED** |
| **Clinical Access** (Web Auth Tab / Optometrist) | Verify Clinical Access | "Check Clinical Access" button | `GET` | `/api/v1/users/clinical/review-access` | None | `MessageResponse` | Yes (Verified Pro) | **VERIFIED** |
| **Screening Consent** (`ConsentScreen.tsx` / Web Consent) | Load Current Consent | Step Mount | `GET` | `/api/v1/screening/consent/current` | None | `ConsentStatusResponse` | Yes (Bearer) | **VERIFIED** |
| **Screening Consent** (`ConsentScreen.tsx` / Web Consent) | Accept Legal Consent | "Accept Consent" button | `POST` | `/api/v1/screening/consent/accept` | `{"version": "1.0.0"}` | `ConsentResponse` | Yes (Bearer) | **VERIFIED** |
| **Screening Consent** (`ConsentScreen.tsx` / Web Consent) | Revoke/Withdraw Consent | "Withdraw Consent" button | `POST` | `/api/v1/screening/consent/withdraw` | None | `{"message", "active_sessions_cancelled"}` | Yes (Bearer) | **VERIFIED** |
| **Screening Sessions** (`ScreeningIntroScreen.tsx` / Web Session) | Initialize Session | "Start Screening" button | `POST` | `/api/v1/screening/sessions` | `{"device_info", "notes"}` (optional) | `ScreeningSessionResponse` | Yes (Consented) | **VERIFIED** |
| **Screening Sessions** (`SessionHistoryScreen.tsx` / Web Session) | View Session Timeline | History View Mount | `GET` | `/api/v1/screening/sessions` | Query params: `page`, `page_size`, `status` | `ScreeningSessionListResponse` | Yes (Bearer) | **VERIFIED** |
| **Screening Sessions** (`ActiveSessionScreen.tsx` / Web Session) | Inspect Session Detail | Select Session | `GET` | `/api/v1/screening/sessions/{id}` | None | `ScreeningSessionResponse` | Yes (Owner) | **VERIFIED** |
| **Screening Sessions** (`ActiveSessionScreen.tsx` / Web Session) | Mark Session Completed | "Complete Session" button | `POST` | `/api/v1/screening/sessions/{id}/complete` | None | `ScreeningSessionResponse` | Yes (Owner) | **VERIFIED** |
| **Screening Sessions** (`ActiveSessionScreen.tsx` / Web Session) | Cancel Active Session | "Cancel Session" button | `POST` | `/api/v1/screening/sessions/{id}/cancel` | `{"reason", "notes"}` | `ScreeningSessionResponse` | Yes (Owner) | **VERIFIED** |

---

## 3. Discovered Endpoint Status

- **Implemented & Connected Endpoints:** 19/19 (100% of implemented Phase 1, Phase 2, Phase 2.1, and Phase 3.1 capabilities).
- **Unimplemented / Future Endpoints (Phase 3.2+):**
  - Optotype Acuity Assessment submission (`/api/v1/screening/sessions/{id}/acuity`) — Scheduled for Phase 3.2.
  - Astigmatism Dial / Color Vision checks (`/api/v1/screening/sessions/{id}/tests/*`) — Scheduled for Phase 3.3.
  - Optometrist Prescription Review / Referral Transfer (`/api/v1/clinical/referrals`) — Scheduled for Phase 4.
