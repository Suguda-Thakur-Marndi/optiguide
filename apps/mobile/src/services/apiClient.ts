import Constants from 'expo-constants';
import {
  HealthResponse,
  DatabaseHealthResponse,
  ConsentStatusResponse,
  ConsentResponse,
  ApiScreeningSessionResponse,
  ScreeningSessionListResponse,
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

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
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
      if (error instanceof TypeError && error.message.includes('Network request failed')) {
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
  // Consent Management Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  /**
   * Get server-controlled consent document and user state (GET /api/v1/screening/consent/current)
   */
  public async getScreeningConsent(): Promise<ConsentStatusResponse> {
    return this.request<ConsentStatusResponse>('/api/v1/screening/consent/current');
  }

  /**
   * Accept current consent document (POST /api/v1/screening/consent/accept)
   */
  public async acceptScreeningConsent(version: string): Promise<ConsentResponse> {
    return this.request<ConsentResponse>('/api/v1/screening/consent/accept', {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  }

  /**
   * Withdraw active consent (POST /api/v1/screening/consent/withdraw)
   */
  public async withdrawScreeningConsent(): Promise<{ message: string; success: boolean }> {
    return this.request<{ message: string; success: boolean }>('/api/v1/screening/consent/withdraw', {
      method: 'POST',
    });
  }

  // --------------------------------------------------------------------------
  // Screening Session Lifecycle Endpoints (Phase 3.1)
  // --------------------------------------------------------------------------

  /**
   * Initiate a new screening session (POST /api/v1/screening/sessions)
   */
  public async createScreeningSession(): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>('/api/v1/screening/sessions', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  /**
   * List user's screening sessions (GET /api/v1/screening/sessions)
   */
  public async listScreeningSessions(
    status?: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<ScreeningSessionListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    return this.request<ScreeningSessionListResponse>(`/api/v1/screening/sessions?${params.toString()}`);
  }

  /**
   * Get a screening session by ID (GET /api/v1/screening/sessions/{sessionId})
   */
  public async getScreeningSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}`);
  }

  /**
   * Complete an in-progress screening session (POST /api/v1/screening/sessions/{sessionId}/complete)
   */
  public async completeScreeningSession(sessionId: string): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/complete`, {
      method: 'POST',
    });
  }

  /**
   * Cancel an in-progress screening session (POST /api/v1/screening/sessions/{sessionId}/cancel)
   */
  public async cancelScreeningSession(
    sessionId: string,
    reason?: string
  ): Promise<ApiScreeningSessionResponse> {
    return this.request<ApiScreeningSessionResponse>(`/api/v1/screening/sessions/${sessionId}/cancel`, {
      method: 'POST',
      body: JSON.stringify(reason ? { reason } : {}),
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
