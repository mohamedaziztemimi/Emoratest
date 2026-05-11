/** @type {import('tailwindcss').Config} */
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    "./src/index.css",
    "./src/styles/emoratest-tokens.css",
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          DEFAULT: "var(--et-blue)",
        light: "var(--et-blue-purple)",
        dark: "var(--et-blue)",
        glow: "var(--et-glow-blue)",
        purple: {
          DEFAULT: "var(--et-purple)",
          light: "var(--et-purple)",
          dark: "var(--et-purple)",
          glow: "var(--et-glow-purple)",
        },
        green: {
          DEFAULT: "var(--et-engaged)",
          light: "var(--et-engaged)",
          dark: "var(--et-engaged)",
        },
        red: {
          DEFAULT: "var(--et-frustrated)",
          light: "var(--et-frustrated)",
          dark: "var(--et-frustrated)",
        },
        yellow: {
          DEFAULT: "var(--et-hesitating)",
          light: "var(--et-hesitating)",
          dark: "var(--et-hesitating)",
        },
        amber: {
          DEFAULT: "var(--et-confused)",
          light: "var(--et-confused)",
          dark: "var(--et-confused)",
        },
        gray: {
          DEFAULT: "var(--et-disengaged)",
          light: "var(--et-disengaged)",
          dark: "var(--et-disengaged)",
        },
        bg: {
          DEFAULT: "var(--et-bg-900)",
          light: "var(--et-bg-800)",
          dark: "var(--et-bg-700)",
          card: "var(--et-bg-card)",
          glass: "var(--et-glass-bg)",
        },
        text: {
          primary: "var(--et-text-primary)",
          secondary: "var(--et-text-secondary)",
          muted: "var(--et-text-muted)",
          inverted: "var(--et-text-primary)",
        },
        border: {
          DEFAULT: "var(--et-border)",
        light: "var(--et-border-light)",
          dark: "var(--et-border-dark)",
          glass: "var(--et-glass-border)",
        },
      },
      fontFamily: {
        sans: [
          "'Inter', 'Figtree', 'system-ui', 'sans-serif'",
          "'Fira Code', 'Courier New', 'monospace'",
        ],
      },
      fontSize: {
        xs: "var(--et-font-xs)",
        sm: "var(--et-font-sm)",
        base: "var(--et-font-base)",
        lg: "var(--et-font-lg)",
        xl: "var(--et-font-xl)",
        "2xl": "var(--et-font-2xl)",
        "3xl": "clamp(36px, 6vw, 72px)",
        "4xl": "clamp(48px, 8vw, 96px)",
      },
      borderRadius: {
        DEFAULT: "var(--et-radius-sm)",
        pill: "var(--et-radius-pill)",
        full: "9999px",
        "2xl": "50%",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
        "2xl": "var(--shadow-2xl)",
        glowBlue: "var(--shadow-glow-blue)",
        glowPurple: "var(--shadow-glow-purple)",
        inner: "inset 0 4px 8px rgba(255, 255, 255, 0.15)",
      },
      spacing: {
        xs: "var(--et-space-xs)",
        sm: "var(--et-space-sm)",
        md: "var(--et-space-md)",
        lg: "var(--et-space-lg)",
        xl: "var(--et-space-xl)",
        "2xl": "var(--et-space-2xl)",
      },
      extend: {
        colors: {
          blue: {
            DEFAULT: "var(--et-blue)",
          light: "var(--et-blue-purple)",
            dark: "var(--et-blue)",
          },
          purple: {
            DEFAULT: "var(--et-purple)",
            light: "var(--et-purple)",
            dark: "var(--et-purple)",
          },
          green: {
            DEFAULT: "var(--et-engaged)",
            light: "var(--et-engaged)",
            dark: "var(--et-engaged)",
          },
          red: {
            DEFAULT: "var(--et-frustrated)",
            light: "var(--et-frustrated)",
            dark: "var(--et-frustrated)",
          },
          yellow: {
            DEFAULT: "var(--et-hesitating)",
            light: "var(--et-hesitating)",
            dark: "var(--et-hesitating)",
          },
          amber: {
            DEFAULT: "var(--et-confused)",
            light: "var(--et-confused)",
            dark: "var(--et-confused)",
          },
          gray: {
            DEFAULT: "var(--et-disengaged)",
            light: "var(--et-disengaged)",
            dark: "var(--et-disengaged)",
          },
        },
      },
      animation: {
        "pulse-emotion": "pulse-emotion 2s ease-in-out infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "scroll-reveal": "scroll-reveal 0.6s var(--et-ease-out)",
        "float": "float 6s ease-in-out infinite",
      },
    },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
    require("tailwind-scrollbar-hide"),
  ],
};

export default config;
