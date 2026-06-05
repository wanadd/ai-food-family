const SLOT_PATTERN = /^\d{4}-\d{2}-\d{2}:(breakfast|lunch|dinner|snack)$/;

/** Decode replaceSlot from URL (handles %3A encoding). */
export function parseReplaceSlot(raw: string | null | undefined): string | null {
  if (!raw?.trim()) {
    return null;
  }
  const decoded = decodeURIComponent(raw.trim());
  return SLOT_PATTERN.test(decoded) ? decoded : null;
}

export function parseCurrentRecipeId(raw: string | null | undefined): number | null {
  if (!raw?.trim()) {
    return null;
  }
  const id = Number(raw);
  return Number.isFinite(id) && id > 0 ? id : null;
}

export function buildReplaceCatalogUrl(
  slotId: string,
  currentRecipeId?: number | null,
): string {
  const params = new URLSearchParams();
  params.set("replaceSlot", slotId);
  if (currentRecipeId != null && currentRecipeId > 0) {
    params.set("currentRecipeId", String(currentRecipeId));
  }
  return `/plan/recipes?${params.toString()}`;
}

export function buildReplaceDetailUrl(
  recipeId: number,
  slotId: string,
  currentRecipeId?: number | null,
): string {
  const params = new URLSearchParams();
  params.set("replaceSlot", slotId);
  if (currentRecipeId != null && currentRecipeId > 0) {
    params.set("currentRecipeId", String(currentRecipeId));
  }
  const qs = params.toString();
  return `/plan/recipes/${recipeId}${qs ? `?${qs}` : ""}`;
}
