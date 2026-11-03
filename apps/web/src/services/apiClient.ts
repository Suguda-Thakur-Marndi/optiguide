import type {
  VisualAcuityCreateRequest,
  VisualAcuityResponse,
  AstigmatismCreateRequest,
  AstigmatismResponse,
  ColorVisionCreateRequest,
  ColorVisionResponse,
  ClinicalSessionSummaryResponse,
} from '@optiguide/shared';
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
        const message = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
        throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
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
    return this.request<ScreeningSessionResponse>(
      '/api/v1/screening/sessions',
      {
        method: 'POST',
        body: JSON.stringify({}),
      },
      true
    );
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
}


export const apiClient = new ApiClient();

// Standalone exports matching previous contracts
export const checkBackendHealth = () => apiClient.checkBackendHealth();
export const checkDatabaseHealth = () => apiClient.checkDatabaseHealth();

export type {
  VisualAcuityCreateRequest,
  VisualAcuityResponse,
  AstigmatismCreateRequest,
  AstigmatismResponse,
  ColorVisionCreateRequest,
  ColorVisionResponse,
  ClinicalSessionSummaryResponse,
};
