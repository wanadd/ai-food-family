import { apiUrl } from "@/lib/api";

import type { ShoppingList } from "./types";

async function shoppingFetch<T>(
  path: string,
  initData: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchShoppingList(
  initData: string,
): Promise<ShoppingList> {
  return shoppingFetch<ShoppingList>("/shopping-lists/me", initData);
}

export async function syncShoppingList(
  initData: string,
): Promise<ShoppingList> {
  return shoppingFetch<ShoppingList>("/shopping-lists/sync", initData, {
    method: "POST",
  });
}

export async function toggleShoppingItem(
  initData: string,
  itemId: string,
  checked: boolean,
): Promise<ShoppingList> {
  return shoppingFetch<ShoppingList>(
    `/shopping-lists/items/${itemId}`,
    initData,
    {
      method: "PATCH",
      body: JSON.stringify({ checked }),
    },
  );
}
