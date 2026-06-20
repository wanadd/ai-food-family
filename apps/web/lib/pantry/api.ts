import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { PantryItem, PantryItemDraft, PantryList } from "./types";

export async function fetchPantry(
  initData: string,
  mode: AppMode,
): Promise<PantryList> {
  return apiFetch<PantryList>(initData, mode, "/pantry/me");
}

export async function addPantryItem(
  initData: string,
  mode: AppMode,
  draft: PantryItemDraft,
): Promise<PantryItem> {
  return apiFetch<PantryItem>(initData, mode, "/pantry/items", {
    method: "POST",
    body: JSON.stringify({
      name: draft.name.trim(),
      category: draft.category.trim() || "другое",
      quantity: draft.quantity.trim(),
      unit: draft.unit.trim() || "шт",
      expires_at: draft.expires_at || null,
      note: draft.note.trim() || null,
      source: "manual",
    }),
  });
}

export async function updatePantryItem(
  initData: string,
  mode: AppMode,
  itemId: number,
  draft: Partial<PantryItemDraft>,
): Promise<PantryItem> {
  return apiFetch<PantryItem>(initData, mode, `/pantry/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: draft.name?.trim(),
      category: draft.category?.trim(),
      quantity: draft.quantity?.trim(),
      unit: draft.unit?.trim(),
      expires_at: draft.expires_at || null,
      note: draft.note?.trim() || null,
    }),
  });
}

export async function deletePantryItem(
  initData: string,
  mode: AppMode,
  itemId: number,
): Promise<void> {
  await apiFetch<void>(initData, mode, `/pantry/items/${itemId}`, {
    method: "DELETE",
  });
}
