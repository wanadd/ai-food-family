/**
 * Conservative pantry ↔ recipe ingredient matching (Sprint 1.8F).
 * Exact normalized name + simple singular/plural variants only — no fuzzy substring.
 */

export type IngredientPantryStatus = "home" | "buy" | "unknown";

function normalizeKey(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, " ");
}

/** Minimal RU plural/singular keys for exact-set lookup. */
function nameVariants(key: string): string[] {
  const out = new Set<string>([key]);
  if (key.length < 3) {
    return Array.from(out);
  }
  if (key.endsWith("и")) {
    out.add(`${key.slice(0, -1)}а`);
    out.add(key.slice(0, -1));
  }
  if (key.endsWith("ы")) {
    out.add(key.slice(0, -1));
    out.add(`${key.slice(0, -1)}а`);
  }
  if (key.endsWith("а")) {
    out.add(`${key.slice(0, -1)}и`);
    out.add(key.slice(0, -1));
  }
  if (key.endsWith("я")) {
    out.add(`${key.slice(0, -1)}е`);
  }
  if (!key.endsWith("а") && !key.endsWith("ы") && !key.endsWith("и")) {
    out.add(`${key}а`);
    out.add(`${key}ы`);
  }
  return Array.from(out);
}

export function buildPantryNameIndex(pantryNames: readonly string[]): Set<string> {
  const index = new Set<string>();
  for (const raw of pantryNames) {
    const key = normalizeKey(raw);
    if (!key) {
      continue;
    }
    for (const variant of nameVariants(key)) {
      index.add(variant);
    }
  }
  return index;
}

export function isIngredientInPantry(
  ingredientName: string,
  pantryIndex: Set<string>,
): boolean {
  const key = normalizeKey(ingredientName);
  if (!key) {
    return false;
  }
  for (const variant of nameVariants(key)) {
    if (pantryIndex.has(variant)) {
      return true;
    }
  }
  return false;
}

export function getIngredientPantryStatus(
  ingredientName: string,
  pantryIndex: Set<string> | null,
): IngredientPantryStatus {
  if (pantryIndex === null) {
    return "unknown";
  }
  return isIngredientInPantry(ingredientName, pantryIndex) ? "home" : "buy";
}
