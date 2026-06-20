/**
 * PLANAM V2 — frontend-level product taxonomy guard.
 *
 * Защитный слой отображения продуктов: нормализация имён, безопасные
 * категории, фильтр подозрительных единиц (твёрдый продукт + л/мл).
 * Не меняет данные на сервере — только то, что видит пользователь.
 *
 * @see reports/product_taxonomy_ui_guard_report.md
 */

// Relative imports keep this module runnable in vitest without a path-alias config.
import {
  normalizeCategorySlug,
  suggestCategorySlug,
} from "../shopping/category-suggest";
import {
  formatProductQuantity as baseFormatProductQuantity,
  type ProductQuantityInput,
} from "./formatProductQuantity";

export type { ProductQuantityInput };

/** Trim + collapse whitespace; первая буква заглавная для отображения. */
export function normalizeProductName(name: string | null | undefined): string {
  const text = (name ?? "").replace(/\s+/g, " ").trim();
  if (!text) {
    return "";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Canonical category slug для продукта.
 * Backend-категория уважается, если она канонична; явно странные/legacy
 * слаги переопределяются по имени продукта.
 */
export function detectProductCategory(
  name: string,
  currentCategory?: string | null,
): string {
  return normalizeCategorySlug(currentCategory ?? null, name);
}

/** Продукты, которые не бывают жидкими (для unit-guard). */
const SOLID_PRODUCT_PATTERNS: RegExp[] = [
  /капуст|огурц|помидор|морков|лук|чеснок|перец|салат|зелень|укроп|петрушк|брокколи|кабач|баклаж|свекл|редис|картоф/i,
  /яблок|груш|банан|апельсин|мандарин|лимон|виноград|персик|слив|арбуз|дын/i,
  /колбас|сосиск|ветчин|бекон|свинин|говядин|телят|баран|курин|куриц|индейк|фарш|мяс|стейк|ребр|окорок|грудк/i,
  /лосос|форел|треск|минтай|сельд|кревет|кальмар|рыб/i,
  /сыр(?!ок\s*плавл)|творог/i,
  /яйц/i,
  /хлеб|батон|булк|лаваш/i,
  /рис|греч|овсян|макарон|спагетти|перлов|пшено|булгур|киноа|мук|сахар|орех/i,
];

const LIQUID_UNITS = new Set(["л", "мл", "l", "ml"]);

/** Жидкие продукты — для них л/мл валидны. */
const LIQUID_PRODUCT_PATTERNS: RegExp[] = [
  /молок|кефир|ряженк|сливк|йогурт\s*питьев/i,
  /вода|сок|чай|кофе|компот|лимонад|квас|напит/i,
  /масло|соус|кетчуп|майонез|уксус|сироп|мёд|мед\b/i,
  /бульон|суп\b/i,
];

/**
 * True, если сочетание «продукт + единица» выглядит как мусор данных
 * (твёрдый продукт с объёмной единицей: «капуста 1 л»).
 */
export function isSuspiciousUnit(
  name: string | null | undefined,
  unit: string | null | undefined,
): boolean {
  const u = (unit ?? "").trim().toLowerCase();
  if (!u || !LIQUID_UNITS.has(u)) {
    return false;
  }
  const n = (name ?? "").trim();
  if (!n) {
    return false;
  }
  if (LIQUID_PRODUCT_PATTERNS.some((p) => p.test(n))) {
    return false;
  }
  return SOLID_PRODUCT_PATTERNS.some((p) => p.test(n));
}

/** Единица внутри уже отформатированной строки количества («1 л» → «л»). */
function extractUnitFromQuantityLine(line: string): string | null {
  const match = line.trim().match(/([a-zа-яё]+)\.?\s*$/i);
  return match ? match[1].toLowerCase() : null;
}

/**
 * Безопасная строка количества для UI.
 * Расширяет базовый formatProductQuantity unit-guard'ом:
 * подозрительные «капуста 1 л» схлопываются в пустую строку
 * (лучше показать только название, чем дичь).
 */
export function formatProductQuantity(input: ProductQuantityInput): string {
  const line = baseFormatProductQuantity(input);
  if (!line) {
    return "";
  }
  const unitInLine = extractUnitFromQuantityLine(line);
  if (unitInLine && isSuspiciousUnit(input.name, unitInLine)) {
    return "";
  }
  return line;
}

export { suggestCategorySlug };
