# OptiGuide — Mock Data Removal & Classification Report

**Document:** `docs/integration/MOCK_DATA_REMOVAL_REPORT.md`  
**Status:** AUDITED & VERIFIED  
**Date:** November 3, 2026  

---

## 1. Executive Summary

An exhaustive repository-wide search was conducted across `apps/mobile/src/`, `apps/mobile/app/`, `apps/web/src/`, and `shared/` to inspect all data sources, interceptors, and state fixtures.

Every discovered non-live data source was classified into one of four mandatory categories:
- **Category A:** Test fixture — preserved for unit and regression testing.
- **Category B:** Storybook/demo data — preserved if isolated from production code.
- **Category C:** Development seed data — preserved if explicitly isolated.
- **Category D:** Production mock implementation — removed and replaced with real backend API integration.

---

## 2. Inventory & Classification Findings

| Item / File | Line / Scope | Classification | Description & Action |
| :--- | :--- | :--- | :--- |
| `apps/mobile/__tests__/apiClient.test.ts` | Lines 20, 49, 78, 110 | **Category A (Test fixture)** | Mock responses for `fetch` in Jest unit tests. **PRESERVED** to test HTTP serialization, header injection, and network timeout error handling in isolation. |
| `apps/web/tests/web.test.js` | Lines 16–23 | **Category A (Test fixture)** | Mock storage map for testing local storage token synchronization logic. **PRESERVED** for automated testing. |
| `apps/mobile/app/(auth)/login.tsx` | Statically empty stub | **Category D (Production mock/stub)** | Previous placeholder screen displayed static text without API calls. **REPLACED** with real `apiClient.login()` and `apiClient.register()` integration. |
| `apps/mobile/app/profile/index.tsx` | Statically empty stub | **Category D (Production mock/stub)** | Previous placeholder screen had no user data. **REPLACED** with real `apiClient.getMe()`, `updateProfile()`, `getUserSessions()`, and `logout()`. |
| `apps/mobile/src/screens/HomeScreen.tsx` | "Start Screening (Phase 2)" button | **Category D (Disabled placeholder)** | Button was hardcoded with `disabled={true}` and a no-op handler. **CONNECTED** to real Phase 3.1 Screening flow via `onNavigateToScreening`. |

---

## 3. Production Data Flow Verification

1. **User Authentication:** Both `apps/mobile` and `apps/web` send credentials to `POST /api/v1/auth/login` and `POST /api/v1/auth/register`. No simulated tokens or mock user objects are used.
2. **User Profiles:** Loaded dynamically via `GET /api/v1/users/me`.
3. **Screening Consent:** Live server text and SHA-256 integrity hash fetched via `GET /api/v1/screening/consent/current`.
4. **Screening Sessions:** Created (`POST /api/v1/screening/sessions`), completed, and cancelled against live database records. Empty states are displayed when no sessions exist.
5. **No Production Fallback Mocks:** If the backend is unreachable or an endpoint fails, the UI renders the real error message and empty state rather than masking the failure with fake success data.
