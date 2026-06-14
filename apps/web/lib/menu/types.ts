export type MenuVariantType = "quick" | "economy" | "balanced";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export type MenuMeal = {
  meal_type: MealType;
  name: string;
  display_title?: string | null;
  description: string;
  prep_time_minutes: number;
  calories_estimate?: number | null;
  recipe_id?: number | null;
  slot_id?: string | null;
  servings?: number | null;
  image_url?: string | null;
  hero_image_url?: string | null;
  thumbnail_url?: string | null;
};

export type MenuIngredient = {
  name: string;
  amount: string;
  category?: string | null;
};

export type MenuDayPlan = {
  day_index: number;
  label: string;
  date_iso?: string | null;
  meals: MenuMeal[];
};

export type MenuVariant = {
  variant: MenuVariantType;
  title: string;
  tagline: string;
  explanation: string;
  estimated_daily_cost: string | null;
  total_prep_minutes: number;
  meals: MenuMeal[];
  ingredients: MenuIngredient[];
  plan_days?: number | null;
  days?: MenuDayPlan[] | null;
};

export type MenuGenerateResponse = {
  menus: MenuVariant[];
  scope_mode: string;
  context_label: string;
  family_name: string | null;
  members_count: number;
  generated_with_ai: boolean;
};

export type SelectedMenu = {
  id: number;
  scope_mode: string;
  user_id: number;
  family_id: number | null;
  variant: MenuVariantType;
  menu: MenuVariant;
  selected_at: string;
};
