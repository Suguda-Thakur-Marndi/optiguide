/**
 * User & Authentication Types
 * Conforming to OptiGuide PRD Section 3.1 & Section 4.2
 */

export type UserRole =
  | 'guest'
  | 'individual'
  | 'patient'
  | 'shopkeeper'
  | 'admin'
  | 'optometrist';

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  phoneNumber?: string;
  preferredLanguage: string;
  shopName?: string;
  shopLocation?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthSession {
  accessToken: string;
  refreshToken?: string;
  tokenType: string;
  expiresIn?: number;
  user: UserProfile;
}
