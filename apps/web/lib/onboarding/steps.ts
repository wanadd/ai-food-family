import type { OnboardingStep } from "./types";

export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: "welcome",
    title: "Добро пожаловать",
    subtitle: "Настроим питание под вашу семью за пару минут",
  },
  {
    id: "goals",
    title: "Ваши цели",
    subtitle: "Что важно в питании прямо сейчас?",
  },
  {
    id: "diets",
    title: "Диеты",
    subtitle: "Выберите подходящий формат питания",
  },
  {
    id: "allergies",
    title: "Аллергии",
    subtitle: "Исключим небезопасные продукты",
  },
  {
    id: "restrictions",
    title: "Ограничения",
    subtitle: "Дополнительные правила и предпочтения",
  },
  {
    id: "favoriteFoods",
    title: "Любимые продукты",
    subtitle: "Что хотите видеть в меню чаще",
  },
  {
    id: "dislikedFoods",
    title: "Нелюбимые продукты",
    subtitle: "Чего лучше избегать",
  },
  {
    id: "budget",
    title: "Бюджет",
    subtitle: "Насколько экономным должно быть меню",
  },
  {
    id: "cookingTime",
    title: "Время готовки",
    subtitle: "Сколько времени готовы тратить на блюдо",
  },
];

export const TOTAL_STEPS = ONBOARDING_STEPS.length;
