/**
 * OptiGuide Design Tokens (Mobile & Shared Native)
 * Strictly aligned with OptiGuide PRD Section 2 (Deep forest green, warm ivory, soft stone)
 * and Section 11 (30 Design Restrictions).
 */

export const colors = {
  primary: {
    50: '#EBF3F1',
    100: '#D2E4E0',
    500: '#4F8278', // Muted Teal
    600: '#073F35', // Deep Forest Green (approved primary)
    700: '#092D28', // Deep Green
    900: '#051E1A',
  },
  accent: {
    50: '#F4F9F8',
    500: '#4F8278', // Muted Teal (approved secondary)
    600: '#3D6C63',
    700: '#2A524A',
  },
  neutral: {
    white: '#F7F4EC', // Warm Ivory (Constraint 3: Avoid pure white backgrounds)
    50: '#F7F4EC',   // Warm Ivory
    100: '#E9E5DA',  // Stone (approved surface)
    200: '#D7D2C4',  // Subtle border
    300: '#CBD5E1',
    400: '#8A928B',
    500: '#686F69',  // Secondary Text
    600: '#475569',
    700: '#202823',  // Charcoal (approved text)
    800: '#1A211D',
    900: '#092D28',
  },
  status: {
    success: '#28734F',
    successBg: '#E8F3ED',
    warning: '#B77932',
    warningBg: '#F9F1E6',
    error: '#A9473E',
    errorBg: '#F8ECEB',
    info: '#4F8278',
    infoBg: '#EAF2F0',
  },
} as const;

export const spacing = {
  none: 0,
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
} as const;

export const typography = {
  fontSize: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
} as const;

export const borderRadius = {
  none: 0,
  sm: 4,
  md: 6,
  base: 8,
  lg: 10,
  full: 9999,
} as const;

export const elevation = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  low: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
    borderWidth: 1,
    borderColor: '#D7D2C4',
  },
  medium: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
    borderWidth: 1,
    borderColor: '#D7D2C4',
  },
  high: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
    borderWidth: 2,
    borderColor: '#073F35',
  },
} as const;
