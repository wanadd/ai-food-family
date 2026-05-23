export type SelectOption = { value: string; label: string };

export const VIRTUAL_KIND_OPTIONS: SelectOption[] = [
  { value: "child", label: "Ребёнок" },
  { value: "elder", label: "Пожилой родственник" },
  { value: "other", label: "Другой" },
];

export const NUTRITION_GOAL_OPTIONS: SelectOption[] = [
  { value: "maintain", label: "Поддержание веса" },
  { value: "lose", label: "Похудение" },
  { value: "gain", label: "Набор массы" },
  { value: "healthy", label: "Здоровое питание" },
  { value: "sport", label: "Спортивный режим" },
  { value: "child", label: "Детское питание" },
  { value: "gentle", label: "Щадящее питание" },
  { value: "therapeutic", label: "Лечебное питание" },
  { value: "other", label: "Другое" },
];

export const ALLERGY_OPTIONS: SelectOption[] = [
  { value: "none", label: "Нет аллергий" },
  { value: "gluten", label: "Глютен" },
  { value: "nuts", label: "Орехи" },
  { value: "dairy", label: "Молочные продукты" },
  { value: "eggs", label: "Яйца" },
  { value: "fish", label: "Рыба" },
  { value: "seafood", label: "Морепродукты" },
  { value: "soy", label: "Соя" },
  { value: "honey", label: "Мёд / пчелиные продукты" },
  { value: "citrus", label: "Цитрусовые" },
  { value: "chocolate", label: "Шоколад" },
  { value: "strawberry", label: "Клубника" },
  { value: "other", label: "Другое" },
];

export const RESTRICTION_OPTIONS: SelectOption[] = [
  { value: "none", label: "Без особенностей" },
  { value: "gluten_free", label: "Без глютена" },
  { value: "lactose_free", label: "Без лактозы" },
  { value: "no_sugar", label: "Без сахара" },
  { value: "vegetarian", label: "Вегетарианство" },
  { value: "vegan", label: "Веганство" },
  { value: "keto", label: "Кето" },
  { value: "paleo", label: "Палео" },
  { value: "halal", label: "Халяль" },
  { value: "kosher", label: "Кошер" },
  { value: "pescatarian", label: "Пескетарианство" },
  { value: "low_carb", label: "Низкоуглеводное" },
  { value: "other", label: "Другое" },
];

export const ALLERGY_PRESET_VALUES = new Set(
  ALLERGY_OPTIONS.map((o) => o.value),
);
export const RESTRICTION_PRESET_VALUES = new Set(
  RESTRICTION_OPTIONS.map((o) => o.value),
);
