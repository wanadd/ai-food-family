import type { ShoppingListItem } from "./types";

export function itemAmountLabel(item: ShoppingListItem): string {
  const qty = item.quantity?.trim();
  const unit = item.unit?.trim();
  if (qty) {
    return unit ? `${qty} ${unit}` : qty;
  }
  return item.amount || "";
}
