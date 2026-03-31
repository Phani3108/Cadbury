import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand — Indigo
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        // Trust zones — the product's core visual language
        trust: {
          auto: "#22c55e",      // green-500: auto-approve
          "auto-bg": "#f0fdf4", // green-50
          review: "#f59e0b",    // amber-500: review needed
          "review-bg": "#fffbeb", // amber-50
          block: "#ef4444",     // red-500: blocked/reject
          "block-bg": "#fef2f2", // red-50
        },
        // Neutrals — Slate base
        background: "#f8fafc",  // slate-50
        surface: "#ffffff",
        border: "#e2e8f0",      // slate-200
        "border-strong": "#cbd5e1", // slate-300
        text: {
          primary: "#0f172a",   // slate-900
          secondary: "#475569", // slate-600
          muted: "#94a3b8",     // slate-400
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      fontSize: {
        "2xs": ["10px", "14px"],
      },
      spacing: {
        "4.5": "18px",
        "18": "72px",
        "56": "224px",
        "14": "56px",
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.07)",
        "card-hover": "0 4px 12px 0 rgb(0 0 0 / 0.10), 0 2px 4px -1px rgb(0 0 0 / 0.06)",
        modal: "0 20px 60px -10px rgb(0 0 0 / 0.18)",
        dropdown: "0 8px 30px rgb(0 0 0 / 0.12)",
      },
      animation: {
        "slide-in-top": "slideInTop 0.4s ease forwards",
        "slide-out": "slideOut 0.3s ease forwards",
        "fade-in": "fadeIn 0.2s ease forwards",
        "count-up": "countUp 0.5s ease forwards",
        "pulse-ring": "pulseRing 2s ease-in-out infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        slideInTop: {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideOut: {
          "0%": { opacity: "1", transform: "translateX(0)" },
          "100%": { opacity: "0", transform: "translateX(20px)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        pulseRing: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(0.95)" },
        },
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
