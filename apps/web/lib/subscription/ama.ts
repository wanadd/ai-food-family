export const AMA_ACTION_LABELS: Record<string, string> = {
  nutritionist_ask: "Вопрос нутрициологу",
  menu_generation_extra: "Дополнительная генерация меню",
  menu_replace_dish: "Замена блюда",
  ocr_receipt: "Разбор чека",
  voice_command: "Голосовая команда",
  deep_nutrition_analysis: "Глубокий анализ питания",
  menu_rebuild: "Перестроение меню",
  ai_report: "AI-отчёт",
  recipe_analyze: "AI-оценка рецепта",
  recipe_improve: "Улучшения рецепта",
};

export function formatAmaCost(cost: number): string {
  const n = Math.abs(Math.floor(cost));
  if (n === 1) return "1 Ам";
  if (n >= 2 && n <= 4) return `${n} Ама`;
  return `${n} Амов`;
}

export function getNutritionistAskCost(
  costs: Record<string, number> | undefined,
): number {
  return costs?.nutritionist_ask ?? 2;
}
