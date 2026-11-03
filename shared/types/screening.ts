/**
 * Preliminary Screening Types
 * Compliant with OptiGuide PRD Section 4 & Section 7
 */

export type ScreeningTestType =
  | 'questionnaire'
  | 'distance_vision'
  | 'near_vision'
  | 'astigmatism'
  | 'color_vision'
  | 'pd_estimation';

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

export interface QuestionnaireResponses {
  blurredVision: 'none' | 'mild' | 'moderate' | 'severe';
  difficultyReadingNear: boolean;
  difficultySeeingDistant: boolean;
  eyeStrainOrHeadaches: boolean;
  currentEyewear: 'none' | 'distance' | 'reading' | 'bifocal_progressive';
  symptomDuration: 'less_than_1_month' | '1_to_6_months' | 'more_than_6_months';
  suddenVisionLoss: boolean; // Urgent red flag
  severeEyePainOrFlashes: boolean; // Urgent red flag
  notes?: string;
}

export interface DistanceVisionResult {
  leftEye: VisualAcuityScore;
  rightEye: VisualAcuityScore;
  binocular?: VisualAcuityScore;
  testedDistanceMeters: number;
  unassistedOrCorrected: 'unassisted' | 'with_glasses' | 'with_contacts';
}

export interface NearVisionResult {
  readingAcuityLabel: string; // e.g. "N6 (Standard newsprint)", "N8", "N10"
  readingDistanceCm: number;
  canReadSmallText: boolean;
  clarityRating: 1 | 2 | 3 | 4 | 5;
}

export interface AstigmatismResult {
  sharpMeridianDetected: boolean;
  indicatedAxes?: number[]; // Clock positions or degrees (e.g. 90, 180)
  hasUniformClarity: boolean;
  screeningObservation: string;
}

export interface ColorVisionResult {
  totalPlates: number;
  correctPlates: number;
  deficiencyIndicated: boolean;
  deficiencyType?: 'none' | 'protan_deutan_red_green' | 'unreliable_calibration';
}

export interface PDEstimationResult {
  pupillaryDistanceMm: number; // e.g. 63.0
  monocularLeftMm?: number;
  monocularRightMm?: number;
  confidenceScore: number;     // 0.0 - 1.0
  referenceCardDetected: boolean;
  faceDetected: boolean;
  imageQualityOk: boolean;
}

export interface EyewearRecommendationSummary {
  suggestedLensCategories: Array<{
    id: string;
    title: string;
    description: string;
    benefits: string[];
  }>;
  suggestedFrameShapes: string[];
  estimatedPDMm?: number;
  professionalReferralRequired: boolean;
  referralReason?: string;
  disclaimer: string;
}

export interface ScreeningSession {
  id: string;
  userId: string;
  customerName?: string;
  customerPhone?: string;
  status: ScreeningStatus;
  startedAt: string;
  completedAt?: string;
  preferredLanguage?: string;
  deviceCalibration?: {
    screenResolution: string;
    distanceCm: number;
    brightnessLux?: number;
    cameraAvailable?: boolean;
  };
  results?: {
    leftEye?: VisualAcuityScore;
    rightEye?: VisualAcuityScore;
    binocular?: VisualAcuityScore;
    colorDeficiencyDetected?: boolean;
    astigmatismIndicator?: boolean;
    distanceVision?: DistanceVisionResult;
    nearVision?: NearVisionResult;
    astigmatism?: AstigmatismResult;
    colorVision?: ColorVisionResult;
    pdEstimation?: PDEstimationResult;
  };
  questionnaire?: QuestionnaireResponses;
  recommendations?: EyewearRecommendationSummary;
}
