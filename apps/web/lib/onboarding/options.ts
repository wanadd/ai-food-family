export type SelectOption = { value: string; label: string; hint?: string };

export const GOAL_OPTIONS: SelectOption[] = [
  { value: "health", label: "Здоровье", hint: "Сбалансированное питание" },
  { value: "weight", label: "Контроль веса" },
  { value: "time", label: "Экономия времени" },
  { value: "family", label: "Семейные обеды" },
  { value: "variety", label: "Разнообразие меню" },
  { value: "budget", label: "Экономия бюджета" },
];

export const DIET_OPTIONS: SelectOption[] = [
  { value: "none", label: "Без особенностей" },
  { value: "vegetarian", label: "Вегетарианство" },
  { value: "vegan", label: "Веганство" },
  { value: "keto", label: "Кето" },
  { value: "paleo", label: "Палео" },
  { value: "halal", label: "Халяль" },
  { value: "kosher", label: "Кошер" },
  { value: "pescatarian", label: "Пескетарианство" },
];

export const ALLERGY_OPTIONS: SelectOption[] = [
  { value: "none", label: "Нет аллергий" },
  { value: "nuts", label: "Орехи" },
  { value: "dairy", label: "Молочные" },
  { value: "gluten", label: "Глютен" },
  { value: "eggs", label: "Яйца" },
  { value: "seafood", label: "Морепродукты" },
  { value: "soy", label: "Соя" },
  { value: "honey", label: "Мёд / пчелиные" },
];

export const RESTRICTION_OPTIONS: SelectOption[] = [
  { value: "none", label: "Без ограничений" },
  { value: "low_sugar", label: "Меньше сахара" },
  { value: "low_salt", label: "Меньше соли" },
  { value: "no_pork", label: "Без свинины" },
  { value: "organic", label: "Органические продукты" },
  { value: "no_spicy", label: "Без острого" },
  { value: "kids_friendly", label: "Подходит детям" },
];

export const BUDGET_OPTIONS: SelectOption[] = [
  { value: "economy", label: "Эконом", hint: "До 500 ₽ / день" },
  { value: "medium", label: "Средний", hint: "500–900 ₽ / день" },
  { value: "premium", label: "Премиум", hint: "900+ ₽ / день" },
];

export const COOKING_TIME_OPTIONS: SelectOption[] = [
  { value: "15", label: "До 15 мин" },
  { value: "30", label: "До 30 мин" },
  { value: "45", label: "До 45 мин" },
  { value: "60", label: "До 60 мин" },
  { value: "60plus", label: "60+ мин" },
];
