import { apiUrl } from "@/lib/api";

import type { PantryItem, PantryItemDraft, PantryList } from "./types";

async function pantryFetch<T>(
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

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function fetchPantry(initData: string): Promise<PantryList> {
  return pantryFetch<PantryList>("/pantry/me", initData);
}

export async function addPantryItem(
  initData: string,
  draft: PantryItemDraft,
): Promise<PantryItem> {
  return pantryFetch<PantryItem>("/pantry/items", initData, {
    method: "POST",
    body: JSON.stringify(draft),
  });
}

export async function updatePantryItem(
  initData: string,
  itemId: number,
  draft: Partial<PantryItemDraft>,
): Promise<PantryItem> {
  return pantryFetch<PantryItem>(`/pantry/items/${itemId}`, initData, {
    method: "PATCH",
    body: JSON.stringify(draft),
  });
}

export async function deletePantryItem(
  initData: string,
  itemId: number,
): Promise<void> {
  await pantryFetch<void>(`/pantry/items/${itemId}`, initData, {
    method: "DELETE",
  });
}
