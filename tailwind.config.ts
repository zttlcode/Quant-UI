import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Legacy profit/loss — 语义色，浅色主题 (#16A34A / #DC2626)
        profit: {
          DEFAULT: "#16A34A",
          light: "#22C55E",
          dark: "#15803D",
        },
        loss: {
          DEFAULT: "#DC2626",
          light: "#EF4444",
          dark: "#B91C1C",
        },
        // terminal colors driven by CSS variables (theme-aware)
        terminal: {
          bg: "hsl(var(--terminal-bg) / <alpha-value>)",
          card: "hsl(var(--terminal-card) / <alpha-value>)",
          border: "hsl(var(--terminal-border) / <alpha-value>)",
          text: "hsl(var(--terminal-text) / <alpha-value>)",
          muted: "hsl(var(--terminal-muted) / <alpha-value>)",
        },
        // AI Quant colors driven by CSS variables (theme-aware)
        ai: {
          deep: "hsl(var(--ai-deep) / <alpha-value>)",
          bg: "hsl(var(--ai-bg) / <alpha-value>)",
          card: "hsl(var(--ai-card) / <alpha-value>)",
          elevated: "hsl(var(--ai-elevated) / <alpha-value>)",
          border: "hsl(var(--ai-border) / <alpha-value>)",
        },
        // Accent colors — 仪表盘专业配色
        quant: {
          cyan: "#2563EB",    // Primary blue (唯一强调色)
          green: "#16A34A",   // Success green (盈亏涨)
          amber: "#F59E0B",   // Warning amber
          red: "#DC2626",     // Danger red (盈亏跌)
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 5px rgba(37, 99, 235, 0.2)" },
          "50%": { boxShadow: "0 0 20px rgba(37, 99, 235, 0.4)" },
        },
        "pulse-green": {
          "0%, 100%": { boxShadow: "0 0 5px rgba(22, 163, 74, 0.2)" },
          "50%": { boxShadow: "0 0 18px rgba(22, 163, 74, 0.35)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
        "count-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "flow-right": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "data-rain": {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "10%": { opacity: "0.3" },
          "90%": { opacity: "0.3" },
          "100%": { transform: "translateY(100vh)", opacity: "0" },
        },
        "neural-pulse": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.8" },
          "50%": { transform: "scale(1.3)", opacity: "1" },
        },
        "tilt": {
          "0%, 100%": { transform: "rotateY(0deg) rotateX(0deg)" },
          "50%": { transform: "rotateY(2deg) rotateX(-1deg)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "pulse-green": "pulse-green 2s ease-in-out infinite",
        "float": "float 3s ease-in-out infinite",
        "count-up": "count-up 0.5s ease-out",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "flow-right": "flow-right 2s linear infinite",
        "data-rain": "data-rain 8s linear infinite",
        "neural-pulse": "neural-pulse 2s ease-in-out infinite",
        "tilt": "tilt 6s ease-in-out infinite",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-terminal": "linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)",
        "gradient-deep": "linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 50%, #FFFFFF 100%)",
        "gradient-cyan": "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
        "gradient-green": "linear-gradient(135deg, #16A34A 0%, #15803D 100%)",
        "gradient-hero": "radial-gradient(ellipse at center, rgba(37,99,235,0.04) 0%, rgba(37,99,235,0) 70%)",
      },
      boxShadow: {
        "cyan-glow": "0 0 16px rgba(37, 99, 235, 0.12)",
        "cyan-glow-lg": "0 0 32px rgba(37, 99, 235, 0.18)",
        "green-glow": "0 0 16px rgba(22, 163, 74, 0.12)",
        "glass": "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
