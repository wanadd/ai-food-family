import { readReturnTo, RETURN_TO_PARAM, withReturnTo } from "@/lib/navigation/return-to";

export type RecipeMealContext = {
  mealType: string | null;
  plannedDate: string | null;
  menuSelectionId: number | null;
  dayIndex: number | null;
};

const MEAL_CONTEXT_KEYS = [
  "mealType",
  "plannedDate",
  "menuSelectionId",
  "dayIndex",
] as const;

export function readRecipeMealContext(
  searchParams: URLSearchParams | null | undefined,
): RecipeMealContext {
  if (!searchParams) {
    return {
      mealType: null,
      plannedDate: null,
      menuSelectionId: null,
      dayIndex: null,
    };
  }
  const menuSelectionId = searchParams.get("menuSelectionId");
  const dayIndex = searchParams.get("dayIndex");
  return {
    mealType: searchParams.get("mealType"),
    plannedDate: searchParams.get("plannedDate"),
    menuSelectionId: menuSelectionId ? Number(menuSelectionId) : null,
    dayIndex: dayIndex ? Number(dayIndex) : null,
  };
}

export function recipeCookPath(
  recipeId: number,
  searchParams?: URLSearchParams | null,
): string {
  const params = new URLSearchParams();
  if (searchParams) {
    const returnTo = searchParams.get(RETURN_TO_PARAM);
    if (returnTo) {
      params.set(RETURN_TO_PARAM, returnTo);
    }
    for (const key of MEAL_CONTEXT_KEYS) {
      const value = searchParams.get(key);
      if (value) {
        params.set(key, value);
      }
    }
  }
  const qs = params.toString();
  return `/plan/recipes/${recipeId}/cook${qs ? `?${qs}` : ""}`;
}

export function recipeDetailPathWithContext(
  recipeId: number,
  searchParams?: URLSearchParams | null,
  fallbackReturnTo = "/plan/recipes",
): string {
  const base = `/plan/recipes/${recipeId}`;
  if (!searchParams) {
    return base;
  }
  const returnTo = readReturnTo(searchParams, fallbackReturnTo);
  const params = new URLSearchParams();
  params.set(RETURN_TO_PARAM, returnTo);
  for (const key of MEAL_CONTEXT_KEYS) {
    const value = searchParams.get(key);
    if (value) {
      params.set(key, value);
    }
  }
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

export function withRecipeMealContext(
  path: string,
  ctx: RecipeMealContext,
  returnTo?: string,
): string {
  const [base, query = ""] = path.split("?");
  const params = new URLSearchParams(query);
  if (returnTo) {
    params.set(RETURN_TO_PARAM, returnTo);
  }
  if (ctx.mealType) params.set("mealType", ctx.mealType);
  if (ctx.plannedDate) params.set("plannedDate", ctx.plannedDate);
  if (ctx.menuSelectionId != null) {
    params.set("menuSelectionId", String(ctx.menuSelectionId));
  }
  if (ctx.dayIndex != null) {
    params.set("dayIndex", String(ctx.dayIndex));
  }
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

export { withReturnTo };
