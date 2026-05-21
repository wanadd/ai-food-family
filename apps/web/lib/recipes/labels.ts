export const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};

export const CATEGORY_LABELS: Record<string, string> = {
  soup: "Суп",
  main: "Основное",
  salad: "Салат",
  dessert: "Десерт",
  quick: "Быстрое",
  kids: "Детское",
};

export const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Легко",
  medium: "Средне",
  hard: "Сложно",
};

export const DIET_LABELS: Record<string, string> = {
  vegetarian: "Вегетарианское",
  vegan: "Веганское",
  kids_friendly: "Для детей",
  budget: "Эконом",
  low_sugar: "Без сахара",
  low_salt: "Мало соли",
  pescatarian: "С рыбой",
};

export function mealLabel(value: string): string {
  return MEAL_TYPE_LABELS[value] ?? value;
}

export function categoryLabel(value: string): string {
  return CATEGORY_LABELS[value] ?? value;
}

export function difficultyLabel(value: string): string {
  return DIFFICULTY_LABELS[value] ?? value;
}

export function dietLabel(value: string): string {
  return DIET_LABELS[value] ?? value;
}
