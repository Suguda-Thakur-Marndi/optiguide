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

/**
 * Phase 3.2 & 3.3 Clinical Assessment API Contracts
 */
export interface CalibrationMetadata {
  screen_width_px?: number;
  screen_height_px?: number;
  display_dpi?: number;
  physical_optotype_mm?: number;
  viewing_distance_cm?: number;
  is_verified?: boolean;
}

export interface VisualAcuityCreateRequest {
  test_eye: 'left' | 'right' | 'binocular';
  snellen_fraction: string;
  logmar: number;
  decimal_acuity: number;
  tested_distance_meters?: number;
  unassisted_or_corrected?: 'unassisted' | 'with_glasses' | 'with_contacts';
  near_reading_label?: string | null;
  near_reading_distance_cm?: number | null;
  is_calibrated?: boolean;
  calibration?: CalibrationMetadata | null;
  observations?: string | null;
}

export interface VisualAcuityResponse {
  id: string;
  session_id: string;
  test_eye: string;
  snellen_fraction: string;
  logmar: number;
  decimal_acuity: number;
  tested_distance_meters: number;
  unassisted_or_corrected: string;
  near_reading_label?: string | null;
  near_reading_distance_cm?: number | null;
  is_calibrated: boolean;
  calibration_metadata?: string | null;
  observations?: string | null;
  recorded_at: string;
  created_at: string;
}

export interface AstigmatismCreateRequest {
  chart_type?: string;
  has_uniform_clarity: boolean;
  indicated_axes?: number[] | null;
  sharpest_meridian_hour?: number | null;
  screening_observation?: string | null;
}

export interface AstigmatismResponse {
  id: string;
  session_id: string;
  chart_type: string;
  has_uniform_clarity: boolean;
  indicated_axes?: string | null;
  sharpest_meridian_hour?: number | null;
  screening_observation?: string | null;
  recorded_at: string;
  created_at: string;
}

export interface ColorVisionCreateRequest {
  test_protocol?: string;
  total_plates_presented: number;
  correct_plate_count: number;
  deficiency_indicated: boolean;
  deficiency_type?: string | null;
  responses_detail?: Array<Record<string, unknown>> | null;
}

export interface ColorVisionResponse {
  id: string;
  session_id: string;
  test_protocol: string;
  total_plates_presented: number;
  correct_plate_count: number;
  deficiency_indicated: boolean;
  deficiency_type?: string | null;
  responses_detail?: string | null;
  recorded_at: string;
  created_at: string;
}

export interface ClinicalSessionSummaryResponse {
  session_id: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  referral_recommended: boolean;
  referral_reasons: string[];
  clinical_disclaimer: string;
  visual_acuity_assessments: VisualAcuityResponse[];
  astigmatism_assessments: AstigmatismResponse[];
  color_vision_assessments: ColorVisionResponse[];
}


/**
 * Interactive Adaptive Visual Acuity & Voice Screening Types
 */
export interface AdaptiveCalibrationInput {
  screen_width_px?: number | null;
  screen_height_px?: number | null;
  display_dpi?: number | null;
  viewing_distance_cm?: number | null;
  calibration_method?: string | null;
  is_professionally_supervised?: boolean;
}

export interface AdaptiveAcuityStartRequest {
  test_type?: 'DISTANCE' | 'NEAR';
  test_eye: 'right' | 'left' | 'both';
  optotype_type?: 'TUMBLING_E' | 'SLOAN' | 'LANDOLT_C';
  protocol_version?: string;
  starting_level?: number;
  viewing_distance_meters?: number | null;
  user_reported_occlusion?: boolean;
  calibration?: AdaptiveCalibrationInput | null;
}

export interface OptotypeChallengeResponse {
  test_id: string;
  attempt_sequence: number;
  current_level: number;
  level_snellen: string;
  level_logmar: number;
  optotype_type: 'TUMBLING_E' | 'SLOAN' | 'LANDOLT_C' | string;
  presented_symbol: string;
  choices: string[];
  target_size_arcmin: number;
  target_height_mm?: number | null;
  target_height_px?: number | null;
  test_eye: string;
  test_type: string;
  instructions: string;
}

export interface AdaptiveAcuityResponseRequest {
  attempt_sequence: number;
  user_response: string;
  response_duration_ms?: number | null;
}

export interface AdaptiveAcuityVoiceResponseRequest {
  attempt_sequence: number;
  audio_base64: string;
  response_duration_ms?: number | null;
}

export interface AdaptiveAcuityResultResponse {
  test_id: string;
  session_id: string;
  user_id: string;
  test_type: string;
  test_eye: string;
  optotype_type: string;
  protocol_version: string;
  status: string;
  calibration_status: string;
  is_calibrated: boolean;
  viewing_distance_meters: number;
  user_reported_occlusion: boolean;
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  smallest_resolved_level?: number | null;
  final_snellen?: string | null;
  final_logmar?: number | null;
  final_decimal?: number | null;
  assessment_id?: string | null;
  started_at: string;
  completed_at?: string | null;
  clinical_disclaimer: string;
  validation_status: string;
}

export interface AdaptiveAcuityStepResponse {
  test_id: string;
  attempt_sequence: number;
  test_status: string;
  was_correct: boolean;
  level: number;
  total_attempts: number;
  correct_attempts: number;
  is_test_complete: boolean;
  next_challenge?: OptotypeChallengeResponse | null;
  result_summary?: AdaptiveAcuityResultResponse | null;
}

export interface AdaptiveAcuityVoiceStepResponse {
  test_id: string;
  attempt_sequence: number;
  test_status: string;
  was_correct: boolean | null;
  level: number;
  total_attempts: number;
  correct_attempts: number;
  is_test_complete: boolean;
  input_modality: string;
  recognition_status: string;
  raw_transcript: string;
  recognized_symbol?: string | null;
  transcription_confidence?: number | null;
  stt_provider?: string | null;
  retry_required: boolean;
  feedback_message: string;
  next_challenge?: OptotypeChallengeResponse | null;
  result_summary?: AdaptiveAcuityResultResponse | null;
}
