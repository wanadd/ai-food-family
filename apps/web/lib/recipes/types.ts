export type RecipeIngredient = {
  name: string;
  amount: string;
};

export type RecipeSummary = {
  id: number;
  title: string;
  description: string;
  meal_type: string;
  category: string;
  prep_time_minutes: number;
  cooking_time_minutes?: number;
  servings: number;
  difficulty: string;
  diets: string[];
  tags: string[];
  is_favorited: boolean;
  is_drink?: boolean;
  is_alcoholic?: boolean;
  calories_per_serving?: number | null;
  protein_g?: number | null;
  suitable_for_children?: boolean;
  suitable_for_sport?: boolean;
  suitable_for_event?: boolean;
  fit_level?: "good" | "partial" | "not_recommended" | null;
};

export type RecipeDetail = RecipeSummary & {
  ingredients: RecipeIngredient[];
  steps: string[];
  allergens?: string[];
  restrictions?: string[];
  sugar_g?: number | null;
  caffeine_mg?: number | null;
  alcohol_percent?: number | null;
  created_at: string;
  updated_at?: string | null;
};

export type RecipeList = {
  items: RecipeSummary[];
  total: number;
};

export type FilterOption = {
  value: string;
  label: string;
};

export type RecipeFilters = {
  meal_types: FilterOption[];
  categories: FilterOption[];
  diets: FilterOption[];
  difficulties: FilterOption[];
  max_prep_time: number;
};

export type RecipeQuery = {
  q?: string;
  meal_type?: string;
  category?: string;
  diet?: string;
  difficulty?: string;
  max_prep_time?: number;
  favorites_only?: boolean;
  from_pantry?: boolean;
  for_children?: boolean;
  for_sport?: boolean;
  for_event?: boolean;
  drinks_only?: boolean;
  non_alcoholic?: boolean;
  alcoholic_only?: boolean;
  protein_only?: boolean;
  smoothie_only?: boolean;
  tea_coffee_only?: boolean;
  goal?: string;
};

export type RecommendationReasonCode =
  | "in_pantry"
  | "kids_like"
  | "goal_match"
  | "quick_cooking"
  | "budget_friendly"
  | "high_protein"
  | "low_calorie"
  | "family_approved";

export type RecommendationReason = {
  code: RecommendationReasonCode;
  label: string;
  kind: "positive" | "warning" | "hard_block";
  weight: number;
};

export type RecipeWhy = {
  recipe_id: number;
  summary: string;
  positives: RecommendationReason[];
  warnings: RecommendationReason[];
  hard_blocks: RecommendationReason[];
  score_total: number;
  uses_ai: boolean;
  uses_ama: boolean;
};
