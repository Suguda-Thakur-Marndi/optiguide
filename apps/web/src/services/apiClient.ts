import type {
  VisualAcuityCreateRequest,
  VisualAcuityResponse,
  AstigmatismCreateRequest,
  AstigmatismResponse,
  ColorVisionCreateRequest,
  ColorVisionResponse,
  ClinicalSessionSummaryResponse,
  AdaptiveAcuityStartRequest,
  OptotypeChallengeResponse,
  AdaptiveAcuityResponseRequest,
  AdaptiveAcuityVoiceResponseRequest,
  AdaptiveAcuityResultResponse,
  AdaptiveAcuityStepResponse,
  AdaptiveAcuityVoiceStepResponse,
} from '@optiguide/shared';
import type {
  FrameCategory,
  FrameTryOnAsset,
  TryOnSession,
  TryOnSnapshot,
  FavouriteItem,
} from '../types/tryOn';
/**
 * OptiGuide Web Centralized API Client
 * Fully integrated with FastAPI backend (/api/v1).
 * Features:
 * - Configurable base URL via VITE_API_BASE_URL
 * - Typed request/response contracts
 * - Automatic 401 token refresh queue
 * - Health and database ping telemetry
 * - Full Authentication, Profile, and Screening Session integration
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export interface HealthStatus {
  online: boolean;
  service?: string;
  database?: string;
  latencyMs?: number;
  message?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string | null;
  role: string;
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse extends AuthTokens {
  user: UserResponse;
}

export interface ConsentResponse {
  id: string;
  user_id: string;
  consent_version: string;
  consent_text_hash: string;
  is_accepted: boolean;
  accepted_at: string;
  withdrawn_at?: string | null;
}

export interface ScreeningSessionResponse {
  id: string;
  user_id: string;
  status: 'in_progress' | 'completed' | 'cancelled';
  created_at: string;
  completed_at?: string | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
}

export interface UserSessionAudit {
  id: string;
  created_at: string;
  expires_at?: string;
  is_revoked: boolean;
  user_agent?: string;
  ip_address?: string;
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string | null) => void)[] = [];

  constructor() {
    this.accessToken = localStorage.getItem('optiguide_access_token');
    this.refreshToken = localStorage.getItem('optiguide_refresh_token');
  }

  public getAccessToken(): string | null {
    return this.accessToken;
  }

  public getRefreshToken(): string | null {
    return this.refreshToken;
  }

  public setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('optiguide_access_token', access);
    localStorage.setItem('optiguide_refresh_token', refresh);
  }

  public clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('optiguide_access_token');
    localStorage.removeItem('optiguide_refresh_token');
  }

  private onRefreshed(token: string | null) {
    this.refreshSubscribers.forEach((callback) => callback(token));
    this.refreshSubscribers = [];
  }

  private subscribeTokenRefresh(cb: (token: string | null) => void) {
    this.refreshSubscribers.push(cb);
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requiresAuth: boolean = false
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (requiresAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });

      // Handle 401 Unauthorized for token refresh
      if (response.status === 401 && requiresAuth && this.refreshToken) {
        if (!this.isRefreshing) {
          this.isRefreshing = true;
          try {
            const refreshRes = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
              body: JSON.stringify({ refresh_token: this.refreshToken }),
            });

            if (refreshRes.ok) {
              const newTokens: AuthTokens = await refreshRes.json();
              this.setTokens(newTokens.access_token, newTokens.refresh_token);
              this.isRefreshing = false;
              this.onRefreshed(newTokens.access_token);
              headers['Authorization'] = `Bearer ${newTokens.access_token}`;
              const retryResponse = await fetch(url, { ...options, headers });
              return (await retryResponse.json()) as T;
            } else {
              this.clearTokens();
              this.isRefreshing = false;
              this.onRefreshed(null);
              throw new Error('Session expired. Please log in again.');
            }
          } catch (refreshErr) {
            this.clearTokens();
            this.isRefreshing = false;
            this.onRefreshed(null);
            throw refreshErr;
          }
        }

        // Wait for active refresh
        return new Promise<T>((resolve, reject) => {
          this.subscribeTokenRefresh(async (newToken) => {
            if (!newToken) {
              return reject(new Error('Session refresh failed.'));
            }
            try {
              headers['Authorization'] = `Bearer ${newToken}`;
              const retryRes = await fetch(url, { ...options, headers });
              resolve((await retryRes.json()) as T);
            } catch (err) {
              reject(err);
            }
          });
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let message =
          errorData.error?.message ||
          errorData.detail ||
          errorData.message ||
          `Request failed with status ${response.status}`;
        if (errorData.error?.details && Array.isArray(errorData.error.details) && errorData.error.details.length > 0) {
          const detailMsgs = errorData.error.details
            .map((d: any) => `${d.loc ? d.loc.slice(1).join('.') + ': ' : ''}${d.msg}`)
            .join('; ');
          message = `${message} (${detailMsgs})`;
        }
        const err = new Error(typeof message === 'string' ? message : JSON.stringify(message));
        (err as any).status = response.status;
        (err as any).code = errorData.error?.code;
        (err as any).errorData = errorData;
        throw err;
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: any) {
      throw err;
    }
  }

  // Diagnostics & Health
  public async checkBackendHealth(): Promise<HealthStatus> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${API_BASE_URL}/api/v1/health`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        return { online: true, service: data.service, database: data.database };
      }
      return { online: false, message: `Backend returned status ${res.status}` };
    } catch (err: any) {
      return { online: false, message: err?.message || 'Failed to connect to FastAPI backend on port 8000' };
    }
  }

  public async checkDatabaseHealth(): Promise<{ isConnected: boolean; latencyMs?: number; dbType?: string }> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${API_BASE_URL}/api/v1/health/db`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        return { isConnected: data.status === 'ok', latencyMs: data.latency_ms, dbType: data.database_type };
      }
      return { isConnected: false };
    } catch {
      return { isConnected: false };
    }
  }

  // Authentication
  public async register(payload: { email: string; password: string; full_name: string }): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async refreshTokens(): Promise<AuthTokens> {
    if (!this.refreshToken) throw new Error('No refresh token available');
    const data = await this.request<AuthTokens>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async logout(): Promise<{ message: string }> {
    try {
      if (this.refreshToken) {
        await this.request<{ message: string }>('/api/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });
      }
    } finally {
      this.clearTokens();
    }
    return { message: 'Logged out successfully.' };
  }

  public async logoutAll(): Promise<{ message: string }> {
    try {
      if (this.accessToken) {
        await this.request<{ message: string }>(
          '/api/v1/auth/logout-all',
          { method: 'POST' },
          true
        );
      }
    } finally {
      this.clearTokens();
    }
    return { message: 'All sessions logged out successfully.' };
  }

  // User Management
  public async getMe(): Promise<UserResponse> {
    return this.request<UserResponse>('/api/v1/users/me', { method: 'GET' }, true);
  }

  public async updateProfile(payload: { full_name?: string; phone_number?: string }): Promise<UserResponse> {
    return this.request<UserResponse>('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }, true);
  }

  public async getUserSessions(): Promise<UserSessionAudit[]> {
    return this.request<UserSessionAudit[]>('/api/v1/users/me/sessions', { method: 'GET' }, true);
  }

  public async getClinicalReviewAccess(): Promise<{ has_access: boolean; role: string }> {
    return this.request<{ has_access: boolean; role: string }>(
      '/api/v1/users/me/clinical-review-access',
      { method: 'GET' },
      true
    );
  }

  // Screening Consent
  public async getScreeningConsent(): Promise<{ consent_version: string; consent_text: string }> {
    return this.request<{ consent_version: string; consent_text: string }>(
      '/api/v1/screening/consent',
      { method: 'GET' }
    );
  }

  public async acceptScreeningConsent(version: string = '1.0.0'): Promise<ConsentResponse> {
    return this.request<ConsentResponse>(
      '/api/v1/screening/consent/accept',
      {
        method: 'POST',
        body: JSON.stringify({ version }),
      },
      true
    );
  }

  public async withdrawScreeningConsent(version: string = '1.0.0'): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      '/api/v1/screening/consent/withdraw',
      {
        method: 'POST',
        body: JSON.stringify({ version }),
      },
      true
    );
  }

  // Screening Session Lifecycle
  public async createScreeningSession(): Promise<ScreeningSessionResponse> {
    try {
      return await this.request<ScreeningSessionResponse>(
        '/api/v1/screening/sessions',
        {
          method: 'POST',
          body: JSON.stringify({}),
        },
        true
      );
    } catch (err: any) {
      const is409 =
        err?.status === 409 ||
        err?.code === 'SESSION_ALREADY_ACTIVE' ||
        (err?.message && (err.message.includes('409') || err.message.includes('already in progress') || err.message.includes('SESSION_ALREADY_ACTIVE')));

      if (is409) {
        try {
          const listRes = await this.request<{ items: ScreeningSessionResponse[] }>(
            '/api/v1/screening/sessions?status=in_progress',
            { method: 'GET' },
            true
          );
          if (listRes?.items?.length) {
            for (const s of listRes.items) {
              await this.cancelScreeningSession(s.id, 'Superseded by starting a new screening').catch(() => {});
            }
          }
          return await this.request<ScreeningSessionResponse>(
            '/api/v1/screening/sessions',
            {
              method: 'POST',
              body: JSON.stringify({}),
            },
            true
          );
        } catch {
          // If cancel/re-create fails, retrieve existing in-progress session to continue
          const listRes = await this.request<{ items: ScreeningSessionResponse[] }>(
            '/api/v1/screening/sessions?status=in_progress',
            { method: 'GET' },
            true
          );
          if (listRes?.items?.length) {
            return listRes.items[0];
          }
        }
      }
      throw err;
    }
  }

  public async getScreeningSession(id: string): Promise<ScreeningSessionResponse> {
    return this.request<ScreeningSessionResponse>(
      `/api/v1/screening/sessions/${id}`,
      { method: 'GET' },
      true
    );
  }

  public async completeScreeningSession(id: string): Promise<ScreeningSessionResponse> {
    return this.request<ScreeningSessionResponse>(
      `/api/v1/screening/sessions/${id}/complete`,
      { method: 'POST' },
      true
    );
  }

  public async cancelScreeningSession(id: string, reason?: string): Promise<ScreeningSessionResponse> {
    return this.request<ScreeningSessionResponse>(
      `/api/v1/screening/sessions/${id}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify(reason ? { reason } : {}),
      },
      true
    );
  }

  public async listUserScreeningSessions(): Promise<ScreeningSessionResponse[]> {
    return this.request<ScreeningSessionResponse[]>(
      '/api/v1/screening/sessions',
      { method: 'GET' },
      true
    );
  }

  // Clinical Assessments (Phase 3.2 & 3.3)
  public async recordVisualAcuity(
    sessionId: string,
    payload: VisualAcuityCreateRequest
  ): Promise<VisualAcuityResponse> {
    return this.request<VisualAcuityResponse>(
      `/api/v1/screening/sessions/${sessionId}/acuity`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      true
    );
  }

  public async getVisualAcuity(sessionId: string): Promise<VisualAcuityResponse[]> {
    return this.request<VisualAcuityResponse[]>(
      `/api/v1/screening/sessions/${sessionId}/acuity`,
      { method: 'GET' },
      true
    );
  }

  public async recordAstigmatism(
    sessionId: string,
    payload: AstigmatismCreateRequest
  ): Promise<AstigmatismResponse> {
    return this.request<AstigmatismResponse>(
      `/api/v1/screening/sessions/${sessionId}/astigmatism`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      true
    );
  }

  public async getAstigmatism(sessionId: string): Promise<AstigmatismResponse[]> {
    return this.request<AstigmatismResponse[]>(
      `/api/v1/screening/sessions/${sessionId}/astigmatism`,
      { method: 'GET' },
      true
    );
  }

  public async recordColorVision(
    sessionId: string,
    payload: ColorVisionCreateRequest
  ): Promise<ColorVisionResponse> {
    return this.request<ColorVisionResponse>(
      `/api/v1/screening/sessions/${sessionId}/color-vision`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      true
    );
  }

  public async getColorVision(sessionId: string): Promise<ColorVisionResponse[]> {
    return this.request<ColorVisionResponse[]>(
      `/api/v1/screening/sessions/${sessionId}/color-vision`,
      { method: 'GET' },
      true
    );
  }

  public async getSessionSummary(sessionId: string): Promise<ClinicalSessionSummaryResponse> {
    return this.request<ClinicalSessionSummaryResponse>(
      `/api/v1/screening/sessions/${sessionId}/summary`,
      { method: 'GET' },
      true
    );
  }

  // Interactive Adaptive Visual Acuity & Voice Screening (ISO 8596 / 3-of-4 ATS)
  public async startAdaptiveAcuityTest(
    sessionId: string,
    payload: AdaptiveAcuityStartRequest
  ): Promise<OptotypeChallengeResponse> {
    try {
      return await this.request<OptotypeChallengeResponse>(
        `/api/v1/screening/sessions/${sessionId}/acuity/start`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
        true
      );
    } catch (err: any) {
      const isDuplicate = err?.message && err.message.includes('already in progress');
      if (isDuplicate) {
        const match = err.message.match(/\(Test ID:\s*([a-f0-9\-]+)\)/i);
        if (match && match[1]) {
          const testId = match[1];
          try {
            await this.cancelAdaptiveAcuityTest(testId, 'Superseded by user restarting eye test');
            return await this.request<OptotypeChallengeResponse>(
              `/api/v1/screening/sessions/${sessionId}/acuity/start`,
              {
                method: 'POST',
                body: JSON.stringify(payload),
              },
              true
            );
          } catch {
            return await this.getAdaptiveAcuityChallenge(testId);
          }
        }
      }
      throw err;
    }
  }

  public async getAdaptiveAcuityChallenge(testId: string): Promise<OptotypeChallengeResponse> {
    return this.request<OptotypeChallengeResponse>(
      `/api/v1/screening/acuity/tests/${testId}/next`,
      { method: 'GET' },
      true
    );
  }

  public async submitAdaptiveAcuityResponse(
    testId: string,
    payload: AdaptiveAcuityResponseRequest
  ): Promise<AdaptiveAcuityStepResponse> {
    return this.request<AdaptiveAcuityStepResponse>(
      `/api/v1/screening/acuity/tests/${testId}/response`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      true
    );
  }

  public async submitAdaptiveAcuityVoiceResponse(
    testId: string,
    payload: AdaptiveAcuityVoiceResponseRequest
  ): Promise<AdaptiveAcuityVoiceStepResponse> {
    return this.request<AdaptiveAcuityVoiceStepResponse>(
      `/api/v1/screening/acuity/tests/${testId}/voice-response`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      true
    );
  }

  public async submitAdaptiveAcuityVoiceBlob(
    testId: string,
    attemptSequence: number,
    wavBlob: Blob,
    durationMs?: number
  ): Promise<AdaptiveAcuityVoiceStepResponse> {
    const url = `${API_BASE_URL}/api/v1/screening/acuity/tests/${testId}/voice-response`;
    const formData = new FormData();
    formData.append('file', wavBlob, 'response.wav');
    formData.append('attempt_sequence', attemptSequence.toString());
    if (durationMs !== undefined) {
      formData.append('response_duration_ms', Math.round(durationMs).toString());
    }

    const headers: Record<string, string> = {};
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || err.message || `Voice submission failed with status ${res.status}`;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }

    return (await res.json()) as AdaptiveAcuityVoiceStepResponse;
  }

  public async completeAdaptiveAcuityTest(testId: string): Promise<AdaptiveAcuityResultResponse> {
    return this.request<AdaptiveAcuityResultResponse>(
      `/api/v1/screening/acuity/tests/${testId}/complete`,
      { method: 'POST' },
      true
    );
  }

  public async cancelAdaptiveAcuityTest(
    testId: string,
    reason?: string
  ): Promise<AdaptiveAcuityResultResponse> {
    return this.request<AdaptiveAcuityResultResponse>(
      `/api/v1/screening/acuity/tests/${testId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify(reason ? { reason } : {}),
      },
      true
    );
  }

  public async getAdaptiveAcuityResult(testId: string): Promise<AdaptiveAcuityResultResponse> {
    return this.request<AdaptiveAcuityResultResponse>(
      `/api/v1/screening/acuity/tests/${testId}/result`,
      { method: 'GET' },
      true
    );
  }

  // Ensures active patient authorization for frictionless testing
  public async ensureAuthenticatedPatient(): Promise<UserResponse> {
    if (this.accessToken) {
      try {
        const me = await this.getMe();
        return me;
      } catch {
        // Token invalid, clear and re-provision
        this.clearTokens();
      }
    }

    // Auto-provision guest patient account
    const rand = Math.random().toString(36).substring(2, 9);
    const guestEmail = `patient_${Date.now()}_${rand}@optiguide.org`;
    const regRes = await this.register({
      email: guestEmail,
      password: 'VisionPass2026!',
      full_name: 'OptiGuide Vision Citizen',
    });

    // Accept consent
    try {
      await this.acceptScreeningConsent('1.0.0');
    } catch {
      // Ignore if already active
    }

    return regRes.user;
  }

  // =========================================================================
  // Virtual Eyewear Try-On API Endpoints (/api/v1/eyewear)
  // =========================================================================

  /**
   * Retrieves active eyewear models with AR overlay telemetry and color options.
   */
  public async listTryOnFrames(params?: {
    shape?: string;
    category?: string;
    gender?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<FrameTryOnAsset[]> {
    const query = new URLSearchParams();
    if (params?.shape) query.append('shape', params.shape);
    if (params?.category) query.append('category', params.category);
    if (params?.gender) query.append('gender', params.gender);
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const qs = query.toString();
    const endpoint = `/api/v1/eyewear/frames${qs ? `?${qs}` : ''}`;
    return this.request<FrameTryOnAsset[]>(endpoint);
  }

  /**
   * Returns available eyewear style and rim categories.
   */
  public async listFrameCategories(): Promise<FrameCategory[]> {
    return this.request<FrameCategory[]>('/api/v1/eyewear/frames/categories');
  }

  /**
   * Returns full geometric dimensions, color variants, and AR overlay assets for a frame.
   */
  public async getTryOnFrame(frameId: string): Promise<FrameTryOnAsset> {
    return this.request<FrameTryOnAsset>(`/api/v1/eyewear/frames/${frameId}`);
  }

  /**
   * Returns dedicated try-on asset telemetry including lens center and bridge coordinates.
   */
  public async getFrameTryOnAssets(frameId: string): Promise<FrameTryOnAsset> {
    return this.request<FrameTryOnAsset>(`/api/v1/eyewear/frames/${frameId}/try-on-assets`);
  }

  /**
   * Initializes an interactive AR session tracking frame selections.
   */
  public async createTryOnSession(payload?: {
    screening_session_id?: string;
    selected_product_id?: string;
    selected_color?: string;
    selected_scale?: number;
    selected_offset_y?: number;
    camera_facing?: 'user' | 'environment';
    device_type?: string;
  }): Promise<TryOnSession> {
    return this.request<TryOnSession>('/api/v1/eyewear/try-on/sessions', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  }

  /**
   * Retrieves active session state and current frame selection.
   */
  public async getTryOnSession(sessionId: string): Promise<TryOnSession> {
    return this.request<TryOnSession>(`/api/v1/eyewear/try-on/sessions/${sessionId}`);
  }

  /**
   * Updates the active frame, color, scale, and offset for the AR session.
   */
  public async selectTryOnFrame(
    sessionId: string,
    payload: {
      product_id: string;
      selected_color?: string;
      selected_scale?: number;
      selected_offset_y?: number;
    }
  ): Promise<TryOnSession> {
    return this.request<TryOnSession>(`/api/v1/eyewear/try-on/sessions/${sessionId}/select-frame`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Adds or removes the selected frame from the authenticated customer's favourites list.
   */
  public async toggleFavouriteFrame(
    sessionId: string,
    payload: {
      product_id: string;
      selected_color?: string;
      notes?: string;
    }
  ): Promise<{ action: 'added' | 'removed'; favourite_id?: string; message: string }> {
    return this.request<{ action: 'added' | 'removed'; favourite_id?: string; message: string }>(
      `/api/v1/eyewear/try-on/sessions/${sessionId}/favourite`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  /**
   * Retrieves saved frames for the authenticated patient or shopper.
   */
  public async listFavouriteFrames(): Promise<FavouriteItem[]> {
    return this.request<FavouriteItem[]>('/api/v1/eyewear/try-on/favourites');
  }

  /**
   * Registers a user-initiated try-on snapshot record.
   */
  public async recordTryOnSnapshot(
    sessionId: string,
    payload: {
      product_id?: string;
      selected_color?: string;
      title?: string;
      face_detected?: boolean;
    }
  ): Promise<TryOnSnapshot> {
    return this.request<TryOnSnapshot>(`/api/v1/eyewear/try-on/sessions/${sessionId}/capture`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Gracefully closes the AR try-on session and releases server resources.
   */
  public async endTryOnSession(sessionId: string): Promise<{ status: string; session_id: string; message: string }> {
    return this.request<{ status: string; session_id: string; message: string }>(
      `/api/v1/eyewear/try-on/sessions/${sessionId}`,
      {
        method: 'DELETE',
      }
    );
  }
}


export const apiClient = new ApiClient();

// Standalone exports matching previous contracts
export const checkBackendHealth = () => apiClient.checkBackendHealth();
export const checkDatabaseHealth = () => apiClient.checkDatabaseHealth();

export const listTryOnFrames = (params?: any) => apiClient.listTryOnFrames(params);
export const listFrameCategories = () => apiClient.listFrameCategories();
export const getTryOnFrame = (frameId: string) => apiClient.getTryOnFrame(frameId);
export const createTryOnSession = (payload?: any) => apiClient.createTryOnSession(payload);
export const selectTryOnFrame = (sessionId: string, payload: any) => apiClient.selectTryOnFrame(sessionId, payload);
export const toggleFavouriteFrame = (sessionId: string, payload: any) => apiClient.toggleFavouriteFrame(sessionId, payload);
export const listFavouriteFrames = () => apiClient.listFavouriteFrames();
export const recordTryOnSnapshot = (sessionId: string, payload: any) => apiClient.recordTryOnSnapshot(sessionId, payload);
export const endTryOnSession = (sessionId: string) => apiClient.endTryOnSession(sessionId);

export type {
  VisualAcuityCreateRequest,
  VisualAcuityResponse,
  AstigmatismCreateRequest,
  AstigmatismResponse,
  ColorVisionCreateRequest,
  ColorVisionResponse,
  ClinicalSessionSummaryResponse,
  AdaptiveAcuityStartRequest,
  OptotypeChallengeResponse,
  AdaptiveAcuityResponseRequest,
  AdaptiveAcuityVoiceResponseRequest,
  AdaptiveAcuityResultResponse,
  AdaptiveAcuityStepResponse,
  AdaptiveAcuityVoiceStepResponse,
  FrameCategory,
  FrameTryOnAsset,
  TryOnSession,
  TryOnSnapshot,
  FavouriteItem,
};
