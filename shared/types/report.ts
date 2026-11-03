/**
 * Screening Report & Referral Types
 * Conforming to OptiGuide PRD Section 4.10, 4.11, 4.13
 */

import { DistanceVisionResult, NearVisionResult, AstigmatismResult, ColorVisionResult, PDEstimationResult } from './screening';

export interface CustomerRecord {
  id: string;
  shopId: string;
  fullName: string;
  phoneNumber: string;
  age?: number;
  gender?: string;
  notes?: string;
  registeredAt: string;
  lastScreeningAt?: string;
  totalScreenings: number;
}

export interface EyewearProduct {
  id: string;
  modelName: string;
  brand: string;
  frameType: 'full_rim' | 'semi_rimless' | 'rimless';
  frameShape: 'rectangular' | 'round' | 'aviator' | 'cat_eye' | 'square' | 'oval';
  material: 'acetate' | 'titanium' | 'metal' | 'tr90';
  lensType: 'single_vision' | 'bifocal' | 'progressive' | 'blue_cut';
  priceINR: number;
  faceShapeCompatibility: string[];
  inStock: boolean;
  stockCount: number;
  imageUrl?: string;
  description: string;
}

export interface EyewearOrder {
  id: string;
  orderNumber: string;
  shopId: string;
  customerId: string;
  customerName: string;
  screeningId?: string;
  productId: string;
  productName: string;
  lensType: string;
  estimatedPDMm?: number;
  priceINR: number;
  status: 'pending' | 'in_progress' | 'ready_for_pickup' | 'completed' | 'cancelled';
  createdAt: string;
  notes?: string;
}

export interface ReferralRecord {
  id: string;
  shopId: string;
  customerId: string;
  customerName: string;
  screeningId: string;
  referralReason: string;
  ophthalmologistName?: string;
  hospitalClinicName?: string;
  status: 'pending_visit' | 'visited' | 'resolved' | 'declined';
  referredAt: string;
  followUpDate?: string;
  clinicalNotes?: string;
}

export interface ScreeningReportSummary {
  id: string;
  screeningId: string;
  userId: string;
  customerName?: string;
  customerPhone?: string;
  generatedAt: string;
  disclaimerAccepted: boolean;
  requiresProfessionalReferral: boolean;
  referralReason?: string;
  preliminaryObservations: string[];
  suggestedNextSteps: string[];
  distanceVision?: DistanceVisionResult;
  nearVision?: NearVisionResult;
  astigmatism?: AstigmatismResult;
  colorVision?: ColorVisionResult;
  pdEstimation?: PDEstimationResult;
  eyewearRecommendations: {
    recommendedLensType?: 'single_vision' | 'progressive' | 'blue_light' | 'reading';
    frameFitSuggestions?: string[];
  };
}
