/**
 * Supported Language Codes and Labels
 * PRD Reference: English, Hindi, Odia as primary baseline.
 */

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', isRTL: false },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', isRTL: false },
  { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', isRTL: false },
  { code: 'es', name: 'Spanish', nativeName: 'Español', isRTL: false },
] as const;

export type LanguageCode = typeof SUPPORTED_LANGUAGES[number]['code'];
