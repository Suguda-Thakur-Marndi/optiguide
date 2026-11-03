import { apiClient } from '../src/services/apiClient';

describe('ApiClient', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    apiClient.setBaseUrl('http://test-server:8000');
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('should trim trailing slashes from base URL', () => {
    apiClient.setBaseUrl('http://example.com/api///');
    expect(apiClient.getBaseUrl()).toBe('http://example.com/api');
  });

  it('should fetch root health correctly', async () => {
    const mockHealth = {
      status: 'ok',
      service: 'optiguide-api',
      version: '1.0.0',
      environment: 'test',
      timestamp: '2026-11-02T01:00:00Z',
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (header: string) => (header === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockHealth,
    } as any);

    const result = await apiClient.getRootHealth();
    expect(result).toEqual(mockHealth);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-server:8000/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'application/json',
        }),
      })
    );
  });

  it('should handle API errors and parse error envelope message', async () => {
    const mockError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: [],
      },
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 422,
      headers: {
        get: (header: string) => (header === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockError,
    } as any);

    await expect(apiClient.getV1Health()).rejects.toThrow('Invalid request data');
  });

  it('should handle network connection failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Network request failed'));

    await expect(apiClient.getDatabaseHealth()).rejects.toThrow(
      'Unable to reach backend at http://test-server:8000'
    );
  });

  it('should authenticate user and store access and refresh tokens', async () => {
    const mockAuthResponse = {
      access_token: 'test_access_jwt',
      refresh_token: 'test_refresh_token',
      token_type: 'Bearer',
      expires_in: 900,
      user: {
        id: 'u-123',
        email: 'patient@example.com',
        full_name: 'Test Patient',
        role: 'patient',
        is_active: true,
        is_verified: false,
      },
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockAuthResponse,
    } as any);

    const res = await apiClient.login({ email: 'patient@example.com', password: 'Password123!' });
    expect(res.access_token).toBe('test_access_jwt');
    expect(apiClient.getAuthToken()).toBe('test_access_jwt');
    expect(apiClient.getRefreshToken()).toBe('test_refresh_token');
  });

  it('should inject Authorization Bearer header into protected calls', async () => {
    apiClient.setAuthToken('my_secret_token');

    const mockProfile = {
      id: 'u-123',
      email: 'patient@example.com',
      full_name: 'Test Patient',
      role: 'patient',
      is_active: true,
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockProfile,
    } as any);

    await apiClient.getMe();
    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-server:8000/api/v1/users/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer my_secret_token',
        }),
      })
    );
  });

  it('should clear tokens on logout', async () => {
    apiClient.setTokens('access', 'refresh');

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => ({ message: 'Logged out' }),
    } as any);

    await apiClient.logout();
    expect(apiClient.getAuthToken()).toBeNull();
    expect(apiClient.getRefreshToken()).toBeNull();
  });

  it('should call clinical assessment endpoints with correct URL and payload', async () => {
    apiClient.setAuthToken('clinical_jwt');

    const mockAcuity = { id: 'acuity-1', test_eye: 'right', snellen_fraction: '20/20' };
    const mockAstig = { id: 'astig-1', chart_type: 'clock_dial', has_uniform_clarity: true };
    const mockColor = { id: 'color-1', deficiency_indicated: false };
    const mockSummary = { session_id: 'sess-123', referral_recommended: false, referral_reasons: [] };

    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => mockAcuity,
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => mockAstig,
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => mockColor,
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => mockSummary,
      } as any);

    const acuityRes = await apiClient.recordVisualAcuity('sess-123', {
      test_eye: 'right',
      snellen_fraction: '20/20',
      logmar: 0.0,
      decimal_acuity: 1.0,
    });
    expect(acuityRes).toEqual(mockAcuity);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-server:8000/api/v1/screening/sessions/sess-123/acuity',
      expect.objectContaining({ method: 'POST' })
    );

    const astigRes = await apiClient.recordAstigmatism('sess-123', {
      chart_type: 'clock_dial',
      has_uniform_clarity: true,
    });
    expect(astigRes).toEqual(mockAstig);

    const colorRes = await apiClient.recordColorVision('sess-123', {
      total_plates_presented: 4,
      correct_plate_count: 4,
      deficiency_indicated: false,
    });
    expect(colorRes).toEqual(mockColor);

    const summaryRes = await apiClient.getSessionSummary('sess-123');
    expect(summaryRes).toEqual(mockSummary);
  });
});