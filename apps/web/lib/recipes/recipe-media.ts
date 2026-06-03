/**
 * PLANAM Recipe Media (2026) — sizes per PLANAM_RECIPE_MEDIA_ARCHITECTURE.md
 */

export type RecipeMediaVariant = "grid" | "hero" | "thumb";

const WIDTH: Record<RecipeMediaVariant, number> = {
  grid: 400,
  hero: 1200,
  thumb: 400,
};

/** Next Image `sizes` hints for responsive loading. */
export function recipeImageSizes(variant: RecipeMediaVariant): string {
  switch (variant) {
    case "hero":
      return "100vw";
    case "grid":
      return "(max-width: 512px) 50vw, 200px";
    case "thumb":
      return "72vw";
    default:
      return "100vw";
  }
}

export function recipeAspectClass(variant: RecipeMediaVariant): string {
  switch (variant) {
    case "hero":
      return "aspect-video";
    case "grid":
      return "aspect-square";
    case "thumb":
      return "aspect-[4/3]";
    default:
      return "aspect-square";
  }
}

/**
 * Optional CDN resize query (no-op if URL already has params).
 */
export function optimizeRecipeImageUrl(
  url: string | null | undefined,
  variant: RecipeMediaVariant,
): string | null {
  if (!url?.trim()) {
    return null;
  }
  const trimmed = url.trim();
  if (trimmed.includes("w=") || trimmed.includes("/card_") || trimmed.includes("/thumb_")) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed);
    if (parsed.hostname.includes("cdn.planam")) {
      parsed.searchParams.set("w", String(WIDTH[variant]));
      parsed.searchParams.set("fm", "webp");
      parsed.searchParams.set("q", "80");
      return parsed.toString();
    }
  } catch {
    return trimmed;
  }
  return trimmed;
}

export function hasRecipeImage(url: string | null | undefined): boolean {
  return Boolean(url?.trim());
}
