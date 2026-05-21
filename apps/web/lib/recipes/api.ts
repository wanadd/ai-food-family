import { apiUrl } from "@/lib/api";

import type {
  RecipeDetail,
  RecipeFilters,
  RecipeList,
  RecipeQuery,
} from "./types";

async function recipeFetch<T>(
  path: string,
  initData: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function buildQuery(params: RecipeQuery): string {
  const search = new URLSearchParams();
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.meal_type) {
    search.set("meal_type", params.meal_type);
  }
  if (params.category) {
    search.set("category", params.category);
  }
  if (params.diet) {
    search.set("diet", params.diet);
  }
  if (params.difficulty) {
    search.set("difficulty", params.difficulty);
  }
  if (params.max_prep_time !== undefined) {
    search.set("max_prep_time", String(params.max_prep_time));
  }
  if (params.favorites_only) {
    search.set("favorites_only", "true");
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchRecipeFilters(
  initData: string,
): Promise<RecipeFilters> {
  return recipeFetch<RecipeFilters>("/recipes/filters", initData);
}

export async function fetchRecipes(
  initData: string,
  params: RecipeQuery = {},
): Promise<RecipeList> {
  return recipeFetch<RecipeList>(`/recipes${buildQuery(params)}`, initData);
}

export async function fetchRecipe(
  initData: string,
  recipeId: number,
): Promise<RecipeDetail> {
  return recipeFetch<RecipeDetail>(`/recipes/${recipeId}`, initData);
}

export async function toggleRecipeFavorite(
  initData: string,
  recipeId: number,
): Promise<{ recipe_id: number; is_favorited: boolean }> {
  return recipeFetch(`/recipes/${recipeId}/favorite`, initData, {
    method: "POST",
  });
}
