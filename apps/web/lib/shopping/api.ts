import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  ShoppingCategory,
  ShoppingItemDraft,
  ShoppingList,
} from "./types";

export async function fetchShoppingList(
  initData: string,
  mode: AppMode,
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(initData, mode, "/shopping-lists/me");
}

export async function syncShoppingList(
  initData: string,
  mode: AppMode,
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(initData, mode, "/shopping-lists/sync", {
    method: "POST",
  });
}

export async function fetchShoppingCategories(
  initData: string,
  mode: AppMode,
): Promise<ShoppingCategory[]> {
  return apiFetch<ShoppingCategory[]>(
    initData,
    mode,
    "/shopping-categories",
  );
}

export async function createShoppingCategory(
  initData: string,
  mode: AppMode,
  name: string,
  isFood: boolean,
): Promise<ShoppingCategory> {
  return apiFetch<ShoppingCategory>(initData, mode, "/shopping-categories", {
    method: "POST",
    body: JSON.stringify({ name, is_food: isFood }),
  });
}

export async function createShoppingItem(
  initData: string,
  mode: AppMode,
  draft: ShoppingItemDraft,
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(initData, mode, "/shopping-lists/items", {
    method: "POST",
    body: JSON.stringify({
      name: draft.name,
      category: draft.category,
      quantity: draft.quantity,
      unit: draft.unit,
      note: draft.note || null,
      is_food: draft.is_food,
    }),
  });
}

export async function updateShoppingItem(
  initData: string,
  mode: AppMode,
  itemId: string,
  patch: {
    name?: string;
    category?: string;
    quantity?: string;
    unit?: string;
    note?: string | null;
    checked?: boolean;
    removeFromPantry?: boolean;
  },
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(
    initData,
    mode,
    `/shopping-lists/items/${itemId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        name: patch.name,
        category: patch.category,
        quantity: patch.quantity,
        unit: patch.unit,
        note: patch.note,
        checked: patch.checked,
        remove_from_pantry: patch.removeFromPantry ?? false,
      }),
    },
  );
}

export async function deleteShoppingItem(
  initData: string,
  mode: AppMode,
  itemId: string,
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(
    initData,
    mode,
    `/shopping-lists/items/${itemId}`,
    { method: "DELETE" },
  );
}

export async function toggleShoppingItem(
  initData: string,
  mode: AppMode,
  itemId: string,
  checked: boolean,
  options?: { removeFromPantry?: boolean },
): Promise<ShoppingList> {
  return updateShoppingItem(initData, mode, itemId, {
    checked,
    removeFromPantry: options?.removeFromPantry,
  });
}
