/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0a0e1a", secondary: "#0f172a", tertiary: "#111827" },
        srf: { DEFAULT: "#1e293b", low: "#131a2b", high: "#263044", glass: "rgba(15,23,42,0.75)", hover: "#334155" },
        brd: { DEFAULT: "#1e293b", subtle: "#1a2332", hover: "#475569", active: "#22d3ee" },
        txt: { DEFAULT: "#e2e8f0", secondary: "#94a3b8", muted: "#64748b", bright: "#f8fafc" },
        accent: { cyan: "#22d3ee", blue: "#3b82f6", indigo: "#6366f1", purple: "#a855f7" },
        status: { critical: "#ef4444", high: "#f97316", elevated: "#f59e0b", medium: "#eab308", low: "#22c55e" },
        "critical-bg": "rgba(239,68,68,0.12)", "high-bg": "rgba(249,115,22,0.12)",
        "medium-bg": "rgba(234,179,8,0.12)", "low-bg": "rgba(34,197,94,0.12)",
      },
      fontFamily: { sans: ["Inter","sans-serif"], mono: ["JetBrains Mono","monospace"] },
      spacing: { sidebar: "250px" },
    }
  },
  plugins: [],
}
