/**
 * User & Authentication Types
 * Conforming to OptiGuide PRD Section 3.1 & Section 4.2
 */

export type UserRole =
  | 'guest'
  | 'individual'
  | 'user'
  | 'patient'
  | 'optometrist'
  | 'eye_care_professional'
  | 'shopkeeper'
  | 'admin';

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  phoneNumber?: string;
  preferredLanguage: string;
  isActive?: boolean;
  isVerified?: boolean;
  shopName?: string;
  shopLocation?: string;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string | null;
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  user: UserProfile;
}

/**
 * Backend wire-format API contracts (OAuth 2.0 RFC 6749 snake_case responses)
 */
export interface ApiUserProfileResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  phone_number: string | null;
  preferred_language: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface ApiAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: ApiUserProfileResponse;
}

export interface ApiTokenRefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiSessionItem {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  is_revoked: boolean;
  expires_at: string;
  created_at: string;
  revoked_at: string | null;
}
