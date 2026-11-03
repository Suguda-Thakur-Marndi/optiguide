/**
 * OptiGuide Core Design Tokens
 * Conforming strictly to OptiGuide Frontend PRD Section 2 & Section 11.
 * Visual Direction: Deep forest green, warm ivory, soft stone, and editorial typography.
 */

export const colors = {
  // Brand identity
  forestGreen: '#073F35',
  deepGreen: '#092D28',
  mutedTeal: '#4F8278',
  warmIvory: '#F7F4EC',
  stone: '#E9E5DA',
  stoneLight: '#F0ECE2',
  charcoal: '#202823',
  secondaryText: '#686F69',

  // Semantic Status Tokens
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

  // Structured Palette for UI Scales
  primary: {
    50: '#EBF3F1',
    100: '#D2E4E0',
    200: '#A5C9C1',
    500: '#4F8278', // Muted Teal
    600: '#073F35', // Forest Green
    700: '#073F35', // Forest Green
    800: '#092D28', // Deep Green
    900: '#051E1A',
  },
  accent: {
    50: '#F4F9F8',
    500: '#4F8278',
    600: '#3D6C63',
    700: '#2A524A',
  },
  neutral: {
    white: '#F7F4EC',     // Warm Ivory (Constraint 3)
    background: '#F7F4EC', // Warm Ivory
    surface: '#E9E5DA',    // Stone
    surfaceSubtle: '#F0ECE2',
    border: '#D7D2C4',
    borderSubtle: '#E4DFD3',
    charcoal: '#202823',
    textSecondary: '#686F69',
    textMuted: '#8A928B',
  },
} as const;

export const typography = {
  fontFamily: {
    heading: "'Lora', 'Georgia', 'Newsreader', serif",
    body: "'Source Sans 3', 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
    monospace: "'IBM Plex Mono', 'Courier New', monospace",
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem',// 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
  },
  fontWeight: {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeight: {
    tight: '1.2',
    editorial: '1.35',
    normal: '1.55',
    relaxed: '1.7',
  },
} as const;

export const spacing = {
  none: 0,
  xs: '4px',
  sm: '8px',
  md: '12px',
  base: '16px',
  lg: '20px',
  xl: '24px',
  '2xl': '32px',
  '3xl': '40px',
  '4xl': '48px',
  '5xl': '64px',
} as const;

export const borderRadius = {
  none: '0px',
  sm: '4px',
  md: '6px',
  base: '8px',
  lg: '10px',
} as const;

export const borders = {
  thin: '1px solid #D7D2C4',
  subtle: '1px solid #E4DFD3',
  forest: '1px solid #073F35',
  focused: '2px solid #073F35',
} as const;

