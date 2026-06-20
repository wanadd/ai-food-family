import { formatProductQuantity } from "@/lib/planam/productTaxonomy";

import type { RecipeIngredient } from "./types";

const TO_TASTE_PHRASES = new Set([
  "по вкусу",
  "немного",
  "щепотка",
  "на кончике ножа",
  "по желанию",
  "опционально",
]);

/**
 * Display amount for a recipe ingredient.
 *
 * The backend already sends a correct `amount`, so we trust it. The fallback
 * goes through the V2 taxonomy guard: no «1 л л» dupes, no volume units on
 * solid products, no undefined/null/NaN — and never a fake «шт» default.
 */
export function formatIngredientAmount(ing: RecipeIngredient): string {
  const amount = (ing.amount ?? "").trim();
  if (amount) {
    return amount;
  }
  const quantity = (ing.quantity ?? "").trim();
  if (quantity && TO_TASTE_PHRASES.has(quantity.toLowerCase())) {
    return quantity;
  }
  return formatProductQuantity({
    quantity: ing.quantity,
    unit: ing.unit,
    name: ing.name,
  });
}
