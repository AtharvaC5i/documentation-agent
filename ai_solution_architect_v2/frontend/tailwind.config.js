// tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#F7F5FF",
          navy: "#1B2A5E",
          purple: "#7C5CBF",
          border: "#D4CBF0",
          muted: "#9B93CC",
          faint: "#C4BAE8",
          surface: "#FFFFFF",
          "purple-light": "#F0EBFF",
        },
      },
      fontFamily: {
        serif: ['"DM Serif Display"', "Georgia", "serif"],
        sans: ['"DM Sans"', "sans-serif"],
      },
      boxShadow: {
        purple: "0 4px 16px rgba(124,92,191,0.30)",
        "purple-lg": "0 6px 24px rgba(124,92,191,0.45)",
        green: "0 4px 16px rgba(26,127,90,0.25)",
      },
      keyframes: {
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in-up": "fadeInUp 0.35s ease forwards",
        shimmer: "shimmer 1.5s ease-in-out infinite",
      },
    },
  },
};
