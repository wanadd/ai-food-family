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
  servings: number;
  difficulty: string;
  diets: string[];
  tags: string[];
  is_favorited: boolean;
};

export type RecipeDetail = RecipeSummary & {
  ingredients: RecipeIngredient[];
  steps: string[];
  created_at: string;
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
};
