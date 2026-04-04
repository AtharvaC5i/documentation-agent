/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],

  theme: {
    extend: {
      // ── Colors ────────────────────────────────────────────────────────────
      colors: {
        // Surfaces
        bg: "#fafafa",
        surface: "#ffffff",
        "surface-offset": "#f5f5f5",
        "surface-dynamic": "#efefef",
        divider: "#e5e7eb",
        border: "#d1d5db",

        // Text
        text: {
          DEFAULT: "#0f0f0f",
          muted: "#6b7280",
          faint: "#9ca3af",
          inverse: "#ffffff",
        },

        // Primary (Teal)
        primary: {
          DEFAULT: "#0d7377",
          hover: "#0a5f63",
          active: "#084d50",
          subtle: "#e6f3f3",
        },

        // Semantic — status only, never decoration
        success: {
          DEFAULT: "#16a34a",
          bg: "#f0fdf4",
          border: "#bbf7d0",
          text: "#15803d",
        },
        warning: {
          DEFAULT: "#d97706",
          bg: "#fffbeb",
          border: "#fde68a",
          text: "#b45309",
        },
        danger: {
          DEFAULT: "#dc2626",
          bg: "#fef2f2",
          border: "#fecaca",
          text: "#b91c1c",
        },
        info: {
          DEFAULT: "#2563eb",
          bg: "#eff6ff",
          border: "#bfdbfe",
          text: "#1d4ed8",
        },
      },

      // ── Typography ────────────────────────────────────────────────────────
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        xxs: ["11px", { lineHeight: "16px", letterSpacing: "0.02em" }], // ← was '2xs'
        xs: ["12px", { lineHeight: "16px" }],
        sm: ["13px", { lineHeight: "20px" }],
        base: ["14px", { lineHeight: "22px" }],
        md: ["15px", { lineHeight: "24px" }],
        lg: ["16px", { lineHeight: "24px" }],
        xl: ["18px", { lineHeight: "28px" }],
        "2xl": ["20px", { lineHeight: "28px" }],
      },

      // ── Spacing ───────────────────────────────────────────────────────────
      // 4px base — only extend what Tailwind doesn't cover by default
      spacing: {
        4.5: "18px",
        13: "52px",
        15: "60px",
        18: "72px",
        22: "88px",
      },

      // ── Border radius ─────────────────────────────────────────────────────
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
        xl: "12px",
        "2xl": "16px",
      },

      // ── Shadows ───────────────────────────────────────────────────────────
      // Tone-matched to warm surfaces. Used sparingly — only for elevation.
      boxShadow: {
        sm: "0 1px 2px rgba(15, 15, 15, 0.05)",
        DEFAULT:
          "0 1px 3px rgba(15, 15, 15, 0.07), 0 1px 2px rgba(15, 15, 15, 0.04)",
        md: "0 4px 8px rgba(15, 15, 15, 0.06), 0 2px 4px rgba(15, 15, 15, 0.04)",
        lg: "0 8px 24px rgba(15, 15, 15, 0.08), 0 4px 8px rgba(15, 15, 15, 0.04)",
        none: "none",
      },

      // ── Transitions ───────────────────────────────────────────────────────
      transitionDuration: {
        DEFAULT: "150ms",
        fast: "100ms",
        slow: "250ms",
      },
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.16, 1, 0.3, 1)",
      },

      // ── Max widths ────────────────────────────────────────────────────────
      maxWidth: {
        content: "1024px",
        narrow: "640px",
        form: "560px",
      },

      // ── Ring ──────────────────────────────────────────────────────────────
      ringColor: {
        DEFAULT: "#0d7377",
      },
      ringOffsetColor: {
        DEFAULT: "#fafafa",
      },
    },
  },

  plugins: [],
};
