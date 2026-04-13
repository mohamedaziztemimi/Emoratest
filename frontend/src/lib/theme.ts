/* ────────────────────────────────────────────────────────
   EmoraTest Design System - Typed Theme Constants
   Everything else imports from here
   ──────────────────────────────────────────────────────── */

/* ── EMOTION CONFIGURATION ──────────────────────────────── */

/**
 * Emotion type configuration with display properties
 */
export interface EmotionConfig {
  color: string;
  label: string;
  icon: string;
  gradient: string | null;
}

/**
 * Emotion type to configuration mapping
 */
export const EMOTION_CONFIG: Record<string, EmotionConfig> = {
  confusion: {
    color: "var(--et-confusion)",
    label: "Confusion",
    icon: "😕",
    gradient: null,
  },
  frustration: {
    color: "var(--et-frustration)",
    label: "Frustration",
    icon: "😤",
    gradient: "linear-gradient(135deg, var(--et-frustration) 0%, var(--et-delight) 100%)",
  },
  delight: {
    color: "var(--et-delight)",
    label: "Delight",
    icon: "😊",
    gradient: null,
  },
  anxiety: {
    color: "var(--et-anxiety)",
    label: "Anxiety",
    icon: "😰",
    gradient: null,
  },
  satisfaction: {
    color: "var(--et-satisfaction)",
    label: "Satisfaction",
    icon: "😌",
    gradient: null,
  },
  hesitation: {
    color: "var(--et-hesitation)",
    label: "Hesitation",
    icon: "🤔",
    gradient: null,
  },
  focus: {
    color: "var(--et-focus)",
    label: "Focus",
    icon: "🎯",
    gradient: null,
  },
  "boredom": {
    color: "var(--et-boredom)",
    label: "Boredom",
    icon: "😑",
    gradient: null,
  },
};

/**
 * Get emotion config by type name
 */
export function getEmotionConfig(emotion: string): EmotionConfig {
  return (
    EMOTION_CONFIG[emotion] || {
      color: "var(--et-text-muted)",
      label: emotion,
      icon: "📄",
      gradient: null,
    }
  );
}

/* ── PERSONA CONFIGURATION ──────────────────────────────── */

/**
 * Display name and accent color for persona types
 */
export interface PersonaConfig {
  display: string;
  accentColor: string;
  gradient: string;
}

/**
 * Persona type to configuration mapping (Alex, Jordan, Taylor, Riley archetypes)
 */
export const PERSONA_CONFIG: Record<string, PersonaConfig> = {
  alex: {
    display: "Alex",
    accentColor: "var(--et-blue)",
    gradient: "linear-gradient(135deg, var(--et-blue) 0%, var(--et-purple) 100%)",
  },
  jordan: {
    display: "Jordan",
    accentColor: "var(--et-purple)",
    gradient: "linear-gradient(135deg, var(--et-purple) 0%, #5B24A5 100%)",
  },
  taylor: {
    display: "Taylor",
    accentColor: "var(--et-blue)",
    gradient: "linear-gradient(135deg, var(--et-blue) 0%, var(--et-purple) 100%)",
  },
  riley: {
    display: "Riley",
    accentColor: "var(--et-purple)",
    gradient: "linear-gradient(135deg, var(--et-purple) 0%, #7C3AED 100%)",
  },
};

/**
 * Get persona config by type name
 */
export function getPersonaConfig(persona: string): PersonaConfig {
  return (
    PERSONA_CONFIG[persona] || {
      display: persona,
      accentColor: "var(--et-text-muted)",
      gradient: null,
    }
  );
}

/* ── GRADIENT DEFINITIONS ──────────────────────────────── */

/**
 * Pre-defined gradient strings for consistent usage
 */
export const GRADIENTS = {
  primary: "var(--et-primary-gradient)",
  blue: "linear-gradient(135deg, var(--et-blue) 0%, #60A5FA 100%)",
  purple: "linear-gradient(135deg, var(--et-blue) 0%, var(--et-purple) 100%)",
  green: "linear-gradient(135deg, #34D399 0%, #10B981 100%)",
  red: "linear-gradient(135deg, #EF4444 0%, #F87171 100%)",
  orange: "linear-gradient(135deg, #FCD34D 0%, #F97316 100%)",
  amber: "linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%)",
  success: "linear-gradient(135deg, #10B981 0%, #34D399 100%)",
  warning: "linear-gradient(135deg, #F59E0B 0%, #F97316 100%)",
  error: "linear-gradient(135deg, #EF4444 0%, #F87171 100%)",
  sunset: "linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)",
  midnight: "linear-gradient(180deg, #0A0B0F 0%, #7C3AED 100%)",
  "unset": "linear-gradient(135deg, #FFD966 0%, #FF9F43 100%)",
  "sunset": "linear-gradient(135deg, #FFD966 0%, #FF9F43 100%)",
};

/**
 * Get gradient by name
 */
export function getGradient(name: string): string {
  return GRADIENTS[name as keyof typeof GRADIENTS] || "transparent";
}

/* ── SHADOW DEFINITIONS ──────────────────────────────── */

/**
 * Box shadow definitions for consistent elevation
 */
export const SHADOWS = {
  sm: "0 2px 8px rgba(0, 0, 0, 0.04)",
  md: "0 4px 16px rgba(0, 0, 0, 0.08)",
  lg: "0 8px 32px rgba(0, 0, 0, 0.12)",
  xl: "0 12px 48px rgba(0, 0, 0, 0.16)",
  "2xl": "0 20px 64px rgba(0, 0, 0, 0.24)",
  glowBlue: "0 0 20px 30px rgba(0, 123, 255, 0.4)",
  glowPurple: "0 0 20px 30px rgba(124, 58, 237, 0.4)",
  inner: "inset 0 4px 8px rgba(255, 255, 255, 0.15)",
};

/**
 * Get shadow by name
 */
export function getShadow(name: string): string {
  return SHADOWS[name as keyof typeof SHADOWS] || "none";
}

/* ── BORER RADIUS DEFINITIONS ──────────────────────────────── */

/**
 * Border radius scale for rounded corners
 */
export const RADIUS = {
  none: "0",
  sm: "var(--et-radius-sm)",
  md: "var(--et-radius-md)",
  lg: "var(--et-radius-lg)",
  xl: "var(--et-radius-xl)",
  pill: "var(--et-radius-pill)",
  full: "9999px",
  "2xl": "50%",
};

/**
 * Get radius by name
 */
export function getRadius(name: string): string {
  return RADIUS[name as keyof typeof RADIUS] || "0";
}

/* ── SPACING SCALE ──────────────────────────────────────── */

/**
 * Spacing scale for consistent layout
 */
export const SPACING = {
  xs: "var(--et-space-xs)",
  sm: "var(--et-space-sm)",
  md: "var(--et-space-md)",
  lg: "var(--et-space-lg)",
  xl: "var(--et-space-xl)",
  "2xl": "var(--et-space-2xl)",
};

/**
 * Get spacing by name
 */
export function getSpacing(name: string): string {
  return SPACING[name as keyof typeof SPACING] || "0";
}

/* ── FONT SIZES ──────────────────────────────────────── */

/**
 * Font size scale for text hierarchy
 */
export const FONT_SIZES = {
  xs: "var(--et-font-xs)",
  sm: "var(--et-font-sm)",
  base: "var(--et-font-base)",
  lg: "var(--et-font-lg)",
  xl: "var(--et-font-xl)",
  "2xl": "var(--et-font-2xl)",
  "3xl": "clamp(36px, 6vw, 72px)",
  "4xl": "clamp(48px, 8vw, 96px)",
};

/**
 * Get font size by name
 */
export function getFontSize(name: string): string {
  return FONT_SIZES[name as keyof typeof FONT_SIZES] || "var(--et-font-base)";
}

/* ── DURATION DEFINITIONS ──────────────────────────────── */

/**
 * Transition duration scale for animations
 */
export const DURATION = {
  fast: "var(--et-duration-fast)",
  base: "var(--et-duration-base)",
  slow: "var(--et-duration-slow)",
};

/**
 * Get duration by name
 */
export function getDuration(name: string): string {
  return DURATION[name as keyof typeof DURATION] || "var(--et-duration-base)";
}

/* ── BREAKPOINT CONSTANTS ──────────────────────────────── */

/**
 * Responsive breakpoint values matching Tailwind defaults
 */
export const BREAKPOINTS = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
};

/**
 * Media query helpers
 */
export const media = {
  xs: `@media (max-width: ${BREAKPOINTS.xs}px)`,
  sm: `@media (max-width: ${BREAKPOINTS.sm}px)`,
  md: `@media (max-width: ${BREAKPOINTS.md}px)`,
  lg: `@media (max-width: ${BREAKPOINTS.lg}px)`,
  xl: `@media (max-width: ${BREAKPOINTS.xl}px)`,
};

/**
 * Check if media matches
 */
export const isBelowBreakpoint = (breakpoint: number) => {
  if (typeof window === "undefined") {
    return false;
  }
  return window.innerWidth < breakpoint;
};

/**
 * Breakpoint helpers for useMedia hook
 */
export const BREAKPOINT_QUERIES = [
  { key: "mobile", value: BREAKPOINTS.md, matches: isBelowBreakpoint(BREAKPOINTS.md) },
  { key: "tablet", value: BREAKPOINTS.lg, matches: isBelowBreakpoint(BREAKPOINTS.lg) },
  { key: "desktop", value: BREAKPOINTS.xl, matches: isBelowBreakpoint(BREAKPOINTS.xl) },
];

/**
 * Get media query string
 */
export const getMediaQuery = (breakpoint: number): string => {
  return `@media (max-width: ${breakpoint - 1}px)`;
};

/* ── Z-INDEX DEFINITIONS ──────────────────────────────── */

/**
 * Z-index scale for layer management
 */
export const Z_INDEX = {
  dropdown: 1000,
  sticky: 100,
  modal: 1100,
  tooltip: 1200,
  overlay: 1400,
  navigation: 1500,
  header: 1600,
};

/**
 * Get z-index by name
 */
export function getZIndex(name: keyof typeof Z_INDEX): number {
  return Z_INDEX[name] || "auto";
}

/* ── TRANSITION EASING ──────────────────────────────── */

/**
 * Transition timing functions
 */
export const EASINGS = {
  easeInOut: "cubic-bezier(0.4, 0, 0.2, 1)",
  easeOut: "cubic-bezier(0, 0, 0.2, 1)",
  easeIn: "cubic-bezier(0.4, 0, 0.6, 1)",
  spring: "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
  bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
};

/**
 * Get easing function by name
 */
export function getEasing(name: keyof typeof EASINGS): string {
  return EASINGS[name as keyof typeof EASINGS] || "easeInOut";
}

/* ── UTILITY FUNCTIONS ──────────────────────────────────────── */

/**
 * Format currency value
 */
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
};

/**
 * Format percentage value
 */
export const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format number with K/M suffix
 */
export const formatNumber = (value: number): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toLocaleString();
};

/**
 * Truncate text to max length with ellipsis
 */
export const truncate = (text: string, maxLength: number = 50): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Generate unique ID for component instances
 */
let instanceId = 0;
export const generateId = (prefix: string = "et-"): string => {
  return `${prefix}-${instanceId++}`;
};

/* ── COLOR HELPERS ──────────────────────────────────────── */

/**
 * Get contrast color based on theme mode
 */
export const getContrastColor = (): string => {
  return "var(--et-text-primary)";
};

/**
 * Get readable color for text
 */
export const getReadableTextColor = (backgroundColor: string): string => {
  const hex = backgroundColor.replace("#", "").replace("var(", "");
  if (hex.length !== 6) {
    return "var(--et-text-primary)";
  }
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return (r * 0.299 + g * 0.587 + b * 0.114) > 186 ? "#FFFFFF" : "#000000";
};

/**
 * Get glassmorphism backdrop for cards
 */
export const getGlassBackdrop = (): string => {
  return "var(--et-glass-bg)";
};

/**
 * Get glow effect based on emotion type
 */
export const getEmotionGlow = (emotion: string): string => {
  const config = getEmotionConfig(emotion);
  switch (emotion) {
    case "delight":
      return "0 0 20px 40px rgba(16, 185, 129, 0.3)";
    case "satisfaction":
      return "0 0 15px 30px rgba(16, 185, 129, 0.2)";
    case "frustration":
      return "0 0 25px 50px rgba(239, 68, 68, 0.15)";
    case "anxiety":
      return "0 0 15px 30px rgba(139, 92, 246, 0.2)";
    case "confusion":
      return "0 0 15px 30px rgba(245, 158, 11, 0.1)";
    default:
      return "none";
  }
};

/* ── EXPORT ALL THEME CONSTANTS ──────────────────────────────────────── */

/**
 * Export all theme constants as a single object
 */
export const THEME = {
  colors: EMOTION_CONFIG,
  personas: PERSONA_CONFIG,
  gradients: GRADIENTS,
  shadows: SHADOWS,
  spacing: SPACING,
  radii: RADIUS,
  fontSizes: FONT_SIZES,
  durations: DURATION,
  breakpoints: BREAKPOINTS,
  zIndex: Z_INDEX,
  easings: EASINGS,
  utilities: {
    formatCurrency,
    formatPercent,
    formatNumber,
    truncate,
    generateId,
    getEmotionConfig,
    getPersonaConfig,
    getGradient,
    getShadow,
    getRadius,
    getSpacing,
    getFontSize,
    getDuration,
    getZIndex,
    getContrastColor,
    getReadableTextColor,
    getGlassBackdrop,
    getEmotionGlow,
  },
} as const;
