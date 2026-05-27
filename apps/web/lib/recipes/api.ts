import { apiUrl } from "@/lib/api";
import { apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  CookingEvent,
  MarkCookedPayload,
  RecipeCollection,
  RecipeCollectionDetail,
  RecipeDetail,
  RecipeFilters,
  RecipeHistory,
  RecipeList,
  RecipeQuery,
  RecipeRatePayload,
  RecipeRateResult,
  RecipeWhy,
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
  const boolKeys = [
    "from_pantry",
    "for_children",
    "for_sport",
    "for_event",
    "drinks_only",
    "non_alcoholic",
    "alcoholic_only",
    "protein_only",
    "smoothie_only",
    "tea_coffee_only",
  ] as const;
  for (const key of boolKeys) {
    if (params[key]) {
      search.set(key, "true");
    }
  }
  if (params.goal) {
    search.set("goal", params.goal);
  }
  if (params.scenario) {
    search.set("scenario", params.scenario);
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

export async function fetchRecipeWhy(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeWhy | null> {
  return apiGet<RecipeWhy>(initData, mode, `/recipes/${recipeId}/why`);
}

export async function markRecipeCooked(
  initData: string,
  mode: AppMode,
  recipeId: number,
  payload: MarkCookedPayload = {},
): Promise<CookingEvent> {
  const result = await recipeFetch<CookingEvent>(
    `/recipes/${recipeId}/cooked`,
    initData,
    {
      method: "POST",
      headers: { "X-App-Mode": mode },
      body: JSON.stringify({ source: "manual", ...payload }),
    },
  );
  return result;
}

export async function fetchRecipeHistory(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeHistory | null> {
  return apiGet<RecipeHistory>(initData, mode, `/recipes/${recipeId}/history`);
}

export async function fetchRecipeCollections(
  initData: string,
  mode: AppMode,
): Promise<RecipeCollection[]> {
  const result = await apiGet<RecipeCollection[]>(initData, mode, "/collections");
  return result ?? [];
}

export async function createRecipeCollection(
  initData: string,
  mode: AppMode,
  payload: {
    name: string;
    visibility: "personal" | "family";
    description?: string;
  },
): Promise<RecipeCollection> {
  return recipeFetch<RecipeCollection>("/collections", initData, {
    method: "POST",
    headers: { "X-App-Mode": mode },
    body: JSON.stringify({
      name: payload.name,
      visibility: payload.visibility,
      description: payload.description ?? "",
    }),
  });
}

export async function addRecipeToCollection(
  initData: string,
  mode: AppMode,
  collectionId: number,
  recipeId: number,
): Promise<RecipeCollectionDetail> {
  return recipeFetch<RecipeCollectionDetail>(
    `/collections/${collectionId}/recipes`,
    initData,
    {
      method: "POST",
      headers: { "X-App-Mode": mode },
      body: JSON.stringify({ recipe_ids: [recipeId] }),
    },
  );
}

export async function rateRecipeForFamily(
  initData: string,
  mode: AppMode,
  recipeId: number,
  payload: RecipeRatePayload,
): Promise<RecipeRateResult> {
  return recipeFetch<RecipeRateResult>(`/recipes/${recipeId}/rate`, initData, {
    method: "POST",
    headers: { "X-App-Mode": mode },
    body: JSON.stringify(payload),
  });
}

export async function toggleRecipeFavorite(
  initData: string,
  recipeId: number,
): Promise<{ recipe_id: number; is_favorited: boolean }> {
  return recipeFetch(`/recipes/${recipeId}/favorite`, initData, {
    method: "POST",
  });
}

export async function addRecipeToShopping(
  initData: string,
  recipeId: number,
  servings?: number,
): Promise<void> {
  await recipeFetch(`/recipes/${recipeId}/add-to-shopping`, initData, {
    method: "POST",
    body: JSON.stringify({ servings: servings ?? null }),
  });
}
