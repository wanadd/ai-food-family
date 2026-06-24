/**
 * Safe display string for pantry/shopping product amounts.
 *
 * TODO: upstream data cleanup for solid products with volume units.
 */

export type ProductQuantityInput = {
  quantity?: string | number | null;
  unit?: string | null;
  amount?: string | null;
  name?: string | null;
};

const INVALID_TOKENS = new Set([
  "null",
  "undefined",
  "nan",
  "none",
  "",
]);

function normalizePart(value: string | number | null | undefined): string {
  if (value == null) {
    return "";
  }
  const text = String(value).trim();
  if (!text || INVALID_TOKENS.has(text.toLowerCase())) {
    return "";
  }
  if (text.toLowerCase() === "nan") {
    return "";
  }
  return text;
}

function unitAlreadyInQuantity(quantity: string, unit: string): boolean {
  const q = quantity.toLowerCase();
  const u = unit.toLowerCase().trim();
  if (!u) {
    return false;
  }
  if (q === u || q.endsWith(` ${u}`)) {
    return true;
  }
  // "1л" vs unit "л"
  if (q.endsWith(u) && /\d/.test(q)) {
    return true;
  }
  return false;
}

function looksLikeFormattedAmount(text: string): boolean {
  return /\d/.test(text) && /[a-zа-яё.%/]/i.test(text);
}

function cleanupDuplicateUnit(text: string): string {
  const normalized = text.replace(/\s+/g, " ").trim();
  return normalized.replace(
    /^(\d+(?:[,.]\d+)?)\s*(г|кг|мл|л|шт|уп|упаковка|пачка|банка|бутылка)\s+\2$/i,
    "$1 $2",
  );
}

/**
 * Returns a user-facing quantity line, or empty string when nothing valid to show.
 */
export function formatProductQuantity(input: ProductQuantityInput): string {
  const amount = normalizePart(input.amount);
  if (amount && looksLikeFormattedAmount(amount)) {
    return cleanupDuplicateUnit(amount);
  }

  const quantity = normalizePart(input.quantity);
  const unit = normalizePart(input.unit);

  if (!quantity && !unit) {
    return "";
  }

  if (quantity && unit && unitAlreadyInQuantity(quantity, unit)) {
    return cleanupDuplicateUnit(quantity);
  }

  if (quantity && unit) {
    return cleanupDuplicateUnit(`${quantity} ${unit}`);
  }

  if (quantity) {
    return quantity;
  }

  return "";
}
