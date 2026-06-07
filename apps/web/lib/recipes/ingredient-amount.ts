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
 * The backend already sends a correct `amount`, so we trust it. This is a
 * defensive fallback that builds an amount from quantity/unit WITHOUT ever
 * appending a fake "шт" default.
 */
export function formatIngredientAmount(ing: RecipeIngredient): string {
  const amount = (ing.amount ?? "").trim();
  if (amount) {
    return amount;
  }
  const quantity = (ing.quantity ?? "").trim();
  const unit = (ing.unit ?? "").trim();
  if (quantity && TO_TASTE_PHRASES.has(quantity.toLowerCase())) {
    return quantity;
  }
  if (quantity && unit) {
    return `${quantity} ${unit}`;
  }
  if (quantity) {
    return quantity;
  }
  return unit;
}
