import Constants from 'expo-constants';
import {
  HealthResponse,
  DatabaseHealthResponse,
  ConsentStatusResponse,
  ConsentResponse,
  ApiScreeningSessionResponse,
  ScreeningSessionListResponse,
  ApiAuthResponse,
  ApiUserProfileResponse,
  ApiTokenRefreshResponse,
  ApiSessionItem,
} from '@optiguide/shared';

// Determine initial base URL from Expo Constants or environment variables
const resolveDefaultApiUrl = (): string => {
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    return process.env.EXPO_PUBLIC_API_BASE_URL;
  }
  const extraUrl = Constants.expoConfig?.extra?.apiBaseUrl;
  if (extraUrl) {
    return extraUrl;
  }
  return 'http://localhost:8000';
};

class ApiClient {
  private baseUrl: string;
  private authToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing: boolean = false;

  constructor() {
    this.baseUrl = resolveDefaultApiUrl();
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    // Trim trailing slash for consistent concatenation
    this.baseUrl = url.trim().replace(/\/+$/, '');
  }

  public setAuthToken(token: string | null): void {
    this.authToken = token;
  }

  public getAuthToken(): string | null {
    return this.authToken;
  }

  public setTokens(access: string | null, refresh: string | null): void {
    this.authToken = access;
    this.refreshToken = refresh;
  }

  public getRefreshToken(): string | null {
    return this.refreshToken;
  }

  public clearTokens(): void {
    this.authToken = null;
    this.refreshToken = null;
  }

  private async request<T>(endpoint: string, options?: RequestInit, isRetry: boolean = false): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(this.authToken ? { Authorization: `Bearer ${this.authToken}` } : {}),
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
          // Retry the request once with new token
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
        if (isJson && data.error) {
          throw new Error(data.error.message || `Request failed with status ${response.status}`);
        }
        throw new Error(typeof data === 'string' ? data : `Request failed with status ${response.status}`);
      }

      return data as T;
    } catch (error: any) {
      if (
        error instanceof TypeError &&
        (error.message.includes('Network request failed') || error.message.includes('fetch'))
      ) {
        throw new Error(`Unable to reach backend at ${this.baseUrl}. Please verify your network and server status.`);
      }
      throw error;
    }
  }

  // --------------------------------------------------------------------------
  // System Health Endpoints
  // --------------------------------------------------------------------------

  /**
   * Root service health (GET /health)
   */
  public async getRootHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  /**
   * System composite health with database status (GET /api/v1/health)
   */
  public async getV1Health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/v1/health');
  }

  /**
   * Dedicated database ping diagnostic (GET /api/v1/health/db)
   */
  public async getDatabaseHealth(): Promise<DatabaseHealthResponse> {
    return this.request<DatabaseHealthResponse>('/api/v1/health/db');
  }

  // --------------------------------------------------------------------------
  // Authentication Endpoints
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

  // --------------------------------------------------------------------------
  // User Management Endpoints
  // --------------------------------------------------------------------------

  public async getMe(): Promise<ApiUserProfileResponse> {
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

  public async getClinicalReviewAccess(): Promise<{ status: string; can_review_screenings: boolean }> {
    return this.request<{ status: string; can_review_screenings: boolean }>('/api/v1/users/clinical/review-access');
  }

  // --------------------------------------------------------------------------
  // Consent Management Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  public async getScreeningConsent(): Promise<ConsentStatusResponse> {
    return this.request<ConsentStatusResponse>('/api/v1/screening/consent/current');
  }

  public async acceptScreeningConsent(version: string = '1.0.0'): Promise<ConsentResponse> {
    return this.request<ConsentResponse>('/api/v1/screening/consent/accept', {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  }

  public async withdrawScreeningConsent(): Promise<{ message: string; active_sessions_cancelled: number }> {
    return this.request<{ message: string; active_sessions_cancelled: number }>('/api/v1/screening/consent/withdraw', {
      method: 'POST',
    });
  }

  // --------------------------------------------------------------------------
  // Screening Session Lifecycle Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  public async createScreeningSession(payload?: { device_info?: string; notes?: string }): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>('/api/v1/screening/sessions', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  }

  public async listScreeningSessions(
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ScreeningSessionListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());

    return this.request<ScreeningSessionListResponse>(`/api/v1/screening/sessions?${params.toString()}`);
  }

  public async getScreeningSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}`);
  }

  public async completeScreeningSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/complete`, {
      method: 'POST',
    });
  }

  public async cancelScreeningSession(
    sessionId: string,
    reason: string = 'user_cancelled',
    notes?: string
  ): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason, notes }),
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
