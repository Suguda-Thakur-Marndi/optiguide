import {
  HealthResponse,
  DatabaseHealthResponse,
  ApiAuthResponse,
  ApiUserProfileResponse,
  ConsentStatusResponse,
  ConsentResponse,
  ApiScreeningSessionResponse,
  ScreeningSessionListResponse,
  ApiTokenRefreshResponse,
  ApiSessionItem,
} from '@optiguide/shared';

// Determine initial base URL from Vite environment or default to local FastAPI
const resolveDefaultApiUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).__OPTIGUIDE_API_URL__) {
    return (window as any).__OPTIGUIDE_API_URL__;
  }
  // If Vite environment variable exists
  if ((import.meta as any).env?.VITE_API_BASE_URL) {
    return (import.meta as any).env.VITE_API_BASE_URL;
  }
  return 'http://localhost:8000';
};

export class WebApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing: boolean = false;

  constructor() {
    this.baseUrl = resolveDefaultApiUrl();
    if (typeof window !== 'undefined' && window.localStorage) {
      this.accessToken = localStorage.getItem('optiguide_access_token');
      this.refreshToken = localStorage.getItem('optiguide_refresh_token');
    }
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.trim().replace(/\/+$/, '');
  }

  public setTokens(access: string | null, refresh: string | null): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (typeof window !== 'undefined' && window.localStorage) {
      if (access) {
        localStorage.setItem('optiguide_access_token', access);
      } else {
        localStorage.removeItem('optiguide_access_token');
      }
      if (refresh) {
        localStorage.setItem('optiguide_refresh_token', refresh);
      } else {
        localStorage.removeItem('optiguide_refresh_token');
      }
    }
  }

  public getAccessToken(): string | null {
    return this.accessToken;
  }

  public getRefreshToken(): string | null {
    return this.refreshToken;
  }

  public clearTokens(): void {
    this.setTokens(null, null);
  }

  private async request<T>(endpoint: string, options?: RequestInit, isRetry: boolean = false): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {}),
      ...(options?.headers as Record<string, string>),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized with token refresh if we have a refresh token
      if (
        response.status === 401 &&
        !isRetry &&
        this.refreshToken &&
        !endpoint.includes('/auth/login') &&
        !endpoint.includes('/auth/refresh')
      ) {
        try {
          await this.refreshTokens();
          // Retry original request once
          return this.request<T>(endpoint, options, true);
        } catch (_) {
          this.clearTokens();
          throw new Error('Session expired. Please sign in again.');
        }
      }

      const contentType = response.headers.get('content-type');
      const isJson = contentType && contentType.includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let msg = `Request failed with status ${response.status}`;
        if (isJson && data.error) {
          msg = data.error.message || msg;
        } else if (typeof data === 'string' && data) {
          msg = data;
        }
        const error = new Error(msg);
        (error as any).status = response.status;
        (error as any).data = data;
        throw error;
      }

      return data as T;
    } catch (error: any) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`Unable to reach backend at ${this.baseUrl}. Please verify the FastAPI server is running.`);
      }
      throw error;
    }
  }

  // --------------------------------------------------------------------------
  // System Health Endpoints
  // --------------------------------------------------------------------------

  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/v1/health');
  }

  public async getDatabaseHealth(): Promise<DatabaseHealthResponse> {
    return this.request<DatabaseHealthResponse>('/api/v1/health/db');
  }

  // --------------------------------------------------------------------------
  // Authentication & User Endpoints
  // --------------------------------------------------------------------------

  public async register(payload: {
    email: string;
    password: string;
    full_name: string;
    preferred_language?: string;
  }): Promise<ApiAuthResponse> {
    const data = await this.request<ApiAuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async login(payload: { email: string; password: string }): Promise<ApiAuthResponse> {
    const data = await this.request<ApiAuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async refreshTokens(): Promise<ApiTokenRefreshResponse> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }
    if (this.isRefreshing) {
      throw new Error('Refresh token rotation in progress');
    }
    this.isRefreshing = true;
    try {
      const data = await this.request<ApiTokenRefreshResponse>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      this.setTokens(data.access_token, data.refresh_token);
      return data;
    } finally {
      this.isRefreshing = false;
    }
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
    return { message: 'Logged out successfully' };
  }

  public async logoutAll(): Promise<{ message: string }> {
    try {
      return await this.request<{ message: string }>('/api/v1/auth/logout-all', {
        method: 'POST',
      });
    } finally {
      this.clearTokens();
    }
  }

  public async getCurrentUser(): Promise<ApiUserProfileResponse> {
    return this.request<ApiUserProfileResponse>('/api/v1/users/me');
  }

  public async updateProfile(payload: {
    full_name?: string;
    phone_number?: string;
    preferred_language?: string;
  }): Promise<ApiUserProfileResponse> {
    return this.request<ApiUserProfileResponse>('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  public async getUserSessions(): Promise<ApiSessionItem[]> {
    return this.request<ApiSessionItem[]>('/api/v1/users/me/sessions');
  }

  public async checkClinicalReviewAccess(): Promise<{ status: string; can_review_screenings: boolean; professional_id: string; verification_status: string }> {
    return this.request<{ status: string; can_review_screenings: boolean; professional_id: string; verification_status: string }>('/api/v1/users/clinical/review-access');
  }

  // --------------------------------------------------------------------------
  // Screening Consent Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  public async getConsentCurrent(): Promise<ConsentStatusResponse> {
    return this.request<ConsentStatusResponse>('/api/v1/screening/consent/current');
  }

  public async acceptConsent(version: string = '1.0.0'): Promise<ConsentResponse> {
    return this.request<ConsentResponse>('/api/v1/screening/consent/accept', {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  }

  public async withdrawConsent(): Promise<{ message: string; active_sessions_cancelled: number }> {
    return this.request<{ message: string; active_sessions_cancelled: number }>('/api/v1/screening/consent/withdraw', {
      method: 'POST',
    });
  }

  // --------------------------------------------------------------------------
  // Screening Sessions Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  public async createSession(): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>('/api/v1/screening/sessions', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  public async listSessions(params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<ScreeningSessionListResponse> {
    const q = new URLSearchParams();
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    if (params?.status) q.append('status', params.status);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return this.request<ScreeningSessionListResponse>(`/api/v1/screening/sessions${queryStr}`);
  }

  public async getSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}`);
  }

  public async completeSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/complete`, {
      method: 'POST',
    });
  }

  public async cancelSession(sessionId: string, reason: string = 'user_cancelled', notes?: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason, notes }),
    });
  }
}

export const webApiClient = new WebApiClient();
export default webApiClient;
