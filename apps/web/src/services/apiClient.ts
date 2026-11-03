/**
 * OptiGuide API Client
 * Connects to FastAPI backend (/api/v1) with typed contracts and graceful offline handling.
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export interface HealthStatus {
  online: boolean;
  service?: string;
  database?: string;
  latencyMs?: number;
  message?: string;
}

export const checkBackendHealth = async (): Promise<HealthStatus> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      return {
        online: true,
        service: data.service,
        database: data.database,
      };
    }
    return {
      online: false,
      message: `Backend returned status ${res.status}`,
    };
  } catch (err: any) {
    return {
      online: false,
      message: err?.message || 'Failed to connect to FastAPI backend on port 8000',
    };
  }
};

export const checkDatabaseHealth = async (): Promise<{ isConnected: boolean; latencyMs?: number; dbType?: string }> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${API_BASE_URL}/api/v1/health/db`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      return {
        isConnected: data.status === 'ok',
        latencyMs: data.latency_ms,
        dbType: data.database_type,
      };
    }
    return { isConnected: false };
  } catch {
    return { isConnected: false };
  }
};
