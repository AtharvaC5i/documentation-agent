/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:        "#0b0f1a",
        surface:   "#111827",
        elevated:  "#1a2236",
        overlay:   "#1f2d47",
        sidebar:   "#0d1424",
        border:    "rgba(255,255,255,0.07)",
        primary:   "#3b82f6",
        "primary-bright": "#60a5fa",
        purple:    "#8b5cf6",
        cyan:      "#06b6d4",
        success:   "#10b981",
        warning:   "#f59e0b",
        danger:    "#ef4444",
        "text-primary":   "#f0f4ff",
        "text-secondary": "#94a3b8",
        "text-muted":     "#64748b",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      backgroundImage: {
        "grad":       "linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)",
        "grad-green": "linear-gradient(135deg, #059669, #10b981)",
      },
      animation: {
        "spin-fast":  "spin 0.65s linear infinite",
        "page-in":    "pageIn 0.22s ease-out both",
        "pop-in":     "popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
        "shimmer":    "shimmer 1.8s infinite",
        "pulse-ring": "pulseRing 0.8s ease-out",
      },
      keyframes: {
        pageIn:    { from: { opacity: 0, transform: "translateY(10px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        popIn:     { from: { transform: "scale(0.6)", opacity: 0 }, to: { transform: "scale(1)", opacity: 1 } },
        shimmer:   { to: { left: "200%" } },
        pulseRing: {
          "0%":   { boxShadow: "0 0 0 0 rgba(99,102,241,0.6)" },
          "70%":  { boxShadow: "0 0 0 8px rgba(99,102,241,0)" },
          "100%": { boxShadow: "0 0 12px rgba(99,102,241,0.4)" },
        },
      },
      boxShadow: {
        glow:  "0 0 24px rgba(99,102,241,0.15)",
        grad:  "0 4px 14px rgba(99,102,241,0.35)",
        "grad-hover": "0 6px 20px rgba(99,102,241,0.5)",
      },
    },
  },
  plugins: [],
};
