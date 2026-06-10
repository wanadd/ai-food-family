import type { Config } from "tailwindcss";

/**
 * PlanAm design foundation (Product UI Redesign · Фаза 1).
 *
 * Токены добавляются АДДИТИВНО: новые семантические цвета (cream / sage /
 * olive / graphite / warm), Manrope, мягкие тени и тёплые радиусы. Существующие
 * emerald/stone-классы продолжают работать без изменений — раскатка бренда на
 * экраны идёт в последующих фазах, а не здесь.
 */
const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Тёплый фон и поверхности
        cream: {
          DEFAULT: "#FFFFFF",
          surface: "#FFFFFF",
          deep: "#F6FAF6",
          border: "#E2E8E0",
        },
        // PlanAm V1 brand green — saturated, fresh
        sage: {
          50: "#ECFDF0",
          100: "#D1FAE0",
          200: "#A7F3C0",
          300: "#6EE7A0",
          400: "#4ADE80",
          500: "#2F9E44",
          600: "#248A38",
          700: "#1B6B2C",
          DEFAULT: "#2F9E44",
        },
        // Мягкий оливковый акцент (бейджи, второстепенное)
        olive: {
          DEFAULT: "#B9C49A",
          deep: "#8E9B6C",
        },
        // Тёплый графит — текст и заголовки
        graphite: {
          900: "#2E2C28",
          700: "#4A463F",
          500: "#726C61",
          400: "#A8A296",
          300: "#C9C3B8",
          DEFAULT: "#2E2C28",
        },
        // Тёплый акцент CTA / «срочно» (дозированно)
        warm: {
          DEFAULT: "#D98E5A",
          soft: "#E8B87E",
        },
        /**
         * P0 hotfix: семантические акценты. Основной цвет — зелёный PLANAM
         * (sage). Эти цвета — только акценты (chips, иконки, прогресс),
         * не фоны целых экранов.
         */
        food: {
          DEFAULT: "#E8833A", // food-orange — еда / meal accent
          soft: "#FDEFE2",
        },
        water: {
          DEFAULT: "#3BA7E0", // water-blue — вода
          soft: "#E5F4FC",
        },
        danger: {
          DEFAULT: "#E05A4E", // danger-red — ограничения / ошибки / просрочено
          soft: "#FDEAE8",
        },
        ai: {
          DEFAULT: "#6366F1", // ai-indigo — Pro / AI
          soft: "#EEF0FE",
        },
        energy: {
          DEFAULT: "#F5B82E", // energy-yellow — активность / энергия
          soft: "#FDF4DD",
        },
        /** PLANAM 2026 semantic roles (CSS variables in globals.css). */
        pa: {
          canvas: "var(--pa-bg-canvas)",
          surface: "var(--pa-bg-surface)",
          elevated: "var(--pa-bg-elevated)",
          foreground: "var(--pa-text-primary)",
          muted: "var(--pa-text-secondary)",
          brand: "var(--pa-brand-primary)",
          "brand-strong": "var(--pa-brand-secondary)",
          accent: "var(--pa-accent)",
          success: "var(--pa-success)",
          warning: "var(--pa-warning)",
          error: "var(--pa-error)",
          border: "var(--pa-border)",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-manrope)",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      borderRadius: {
        control: "14px",
        card: "20px",
        pill: "9999px",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(46,44,40,0.04), 0 8px 24px -16px rgba(46,44,40,0.18)",
        card: "0 1px 2px rgba(46,44,40,0.04), 0 12px 32px -20px rgba(46,44,40,0.25)",
        lift: "0 2px 4px rgba(46,44,40,0.06), 0 18px 40px -22px rgba(46,44,40,0.30)",
      },
    },
  },
  plugins: [],
};

export default config;
