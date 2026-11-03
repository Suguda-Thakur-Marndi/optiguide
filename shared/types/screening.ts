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

export type ScreeningStatus = 'pending' | 'in_progress' | 'completed' | 'abandoned';

export interface VisualAcuityScore {
  snellenFraction: string; // e.g. "20/20", "20/40"
  logMAR: number;          // e.g. 0.0, 0.3
  decimal: number;         // e.g. 1.0, 0.5
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
  preferredLanguage: string;
  deviceCalibration: {
    screenResolution: string;
    distanceCm: number;
    brightnessLux?: number;
    cameraAvailable: boolean;
  };
  questionnaire?: QuestionnaireResponses;
  results: {
    distanceVision?: DistanceVisionResult;
    nearVision?: NearVisionResult;
    astigmatism?: AstigmatismResult;
    colorVision?: ColorVisionResult;
    pdEstimation?: PDEstimationResult;
  };
  recommendations?: EyewearRecommendationSummary;
}
