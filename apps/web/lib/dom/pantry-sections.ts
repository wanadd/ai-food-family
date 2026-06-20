import type { PantryItem } from "@/lib/pantry/types";

export type PantryBuckets = {
  current: PantryItem[];
  expiringSoon: PantryItem[];
  excess: PantryItem[];
};

function parseQuantity(value: string): number | null {
  const n = parseFloat(value.replace(",", ".").trim());
  return Number.isFinite(n) ? n : null;
}

/** Heuristic «избыток» без отдельного API. */
export function isExcessPantryItem(item: PantryItem): boolean {
  const n = parseQuantity(item.quantity);
  if (n == null) {
    return false;
  }
  const unit = (item.unit || "").toLowerCase();
  if (unit.includes("кг") && n >= 1) {
    return true;
  }
  if ((unit.includes("л") || unit === "l") && n >= 2) {
    return true;
  }
  return n >= 5;
}

export function splitPantryBuckets(items: PantryItem[]): PantryBuckets {
  const active = items.filter((i) => !i.is_expired);
  const expiringSoon = active.filter(
    (i) => i.expires_at != null && i.days_until_expiry <= 3,
  );
  const expiringIds = new Set(expiringSoon.map((i) => i.id));
  const excess = active.filter(
    (i) => !expiringIds.has(i.id) && isExcessPantryItem(i),
  );
  const excessIds = new Set(excess.map((i) => i.id));
  const current = active.filter(
    (i) => !expiringIds.has(i.id) && !excessIds.has(i.id),
  );
  return { current, expiringSoon, excess };
}
