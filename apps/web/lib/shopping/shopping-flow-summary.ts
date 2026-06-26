import type { PantryItem } from "@/lib/pantry/types";
import type { FromPantryRecipe } from "@/lib/recipes/types";
import type { ShoppingList } from "@/lib/shopping/types";

export type ShoppingFlowStatus = {
  toBuy: number;
  atHome: number;
  dishesCovered: number;
  menuLinkedItems: number;
  menuTitle: string | null;
};

export function computeShoppingFlowStatus(
  list: ShoppingList | null,
  pantryItems: PantryItem[] | null,
  fromPantry: FromPantryRecipe[] | null,
): ShoppingFlowStatus {
  const toBuy = list?.items.filter((i) => !i.checked).length ?? 0;
  const atHome =
    pantryItems?.filter((i) => !i.is_expired).length ?? 0;
  const dishesCovered =
    fromPantry?.filter((r) => r.total > 0 && r.have >= r.total).length ?? 0;
  const menuLinkedItems =
    list?.items.filter(
      (i) => !i.checked && (i.source === "menu" || i.source === "recipe"),
    ).length ?? 0;

  return {
    toBuy,
    atHome,
    dishesCovered,
    menuLinkedItems,
    menuTitle: list?.menu_title ?? null,
  };
}

export function isBoughtToday(checkedAt: string | null): boolean {
  if (!checkedAt) {
    return false;
  }
  const d = new Date(checkedAt);
  if (Number.isNaN(d.getTime())) {
    return false;
  }
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}
