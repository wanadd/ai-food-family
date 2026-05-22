import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { ShoppingList } from "./types";

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

export async function toggleShoppingItem(
  initData: string,
  mode: AppMode,
  itemId: string,
  checked: boolean,
  options?: { removeFromPantry?: boolean },
): Promise<ShoppingList> {
  return apiFetch<ShoppingList>(
    initData,
    mode,
    `/shopping-lists/items/${itemId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        checked,
        remove_from_pantry: options?.removeFromPantry ?? false,
      }),
    },
  );
}
