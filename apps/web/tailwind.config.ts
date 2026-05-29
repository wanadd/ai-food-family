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
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Тёплый фон и поверхности
        cream: {
          DEFAULT: "#FBF7EF",
          surface: "#FFFDF8",
          deep: "#F3EEE2",
          border: "#ECE4D6",
        },
        // Основной брендовый зелёный (шалфей)
        sage: {
          50: "#EEF3EC",
          100: "#DCE8D6",
          200: "#C2D6BA",
          300: "#9CBE90",
          400: "#7DA870",
          500: "#5E8B57",
          600: "#4C7347",
          700: "#3C5B39",
          DEFAULT: "#5E8B57",
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
