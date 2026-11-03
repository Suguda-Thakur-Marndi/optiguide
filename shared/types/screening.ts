/**
 * Preliminary Screening Types
 */

export type ScreeningTestType =
  | 'distance_vision'
  | 'near_vision'
  | 'astigmatism'
  | 'color_vision';

export type ScreeningSessionStatusType = 'in_progress' | 'completed' | 'cancelled';
export type ScreeningStatus = ScreeningSessionStatusType | 'pending' | 'abandoned';

export interface VisualAcuityScore {
  snellenFraction: string; // e.g. "20/20", "20/40"
  logMAR: number; // e.g. 0.0, 0.3
  decimal: number; // e.g. 1.0, 0.5
}

/**
 * Informed Consent Types (Phase 3.1)
 */
export interface ConsentStatusResponse {
  version: string;
  title: string;
  content: string;
  hash: string;
  has_accepted: boolean;
  is_active: boolean;
  accepted_at?: string | null;
  withdrawn_at?: string | null;
}

export interface ConsentAcceptRequest {
  version: string;
}

export interface ConsentResponse {
  id: string;
  user_id: string;
  consent_version: string;
  consent_text_hash: string;
  accepted_at: string;
  withdrawn_at?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Screening Session Types (Phase 3.1)
 */
export interface ScreeningSessionCancelRequest {
  reason?: string;
}

export interface ApiScreeningSessionResponse {
  id: string;
  user_id: string;
  consent_id: string;
  status: ScreeningSessionStatusType;
  cancellation_reason?: string | null;
  started_at: string;
  completed_at?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScreeningSessionListResponse {
  items: ApiScreeningSessionResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface ScreeningSession {
  id: string;
  userId: string;
  status: ScreeningStatus;
  startedAt: string;
  completedAt?: string;
  deviceCalibration?: {
    screenResolution: string;
    distanceCm: number;
    brightnessLux?: number;
  };
  results?: {
    leftEye?: VisualAcuityScore;
    rightEye?: VisualAcuityScore;
    binocular?: VisualAcuityScore;
    colorDeficiencyDetected?: boolean;
    astigmatismIndicator?: boolean;
  };
}
