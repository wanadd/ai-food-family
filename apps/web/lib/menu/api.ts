import { apiUrl } from "@/lib/api";

import type {
  MenuGenerateResponse,
  MenuVariant,
  SelectedMenu,
} from "./types";

async function menuFetch<T>(
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

export async function generateMenus(
  initData: string,
): Promise<MenuGenerateResponse> {
  return menuFetch<MenuGenerateResponse>("/menus/generate", initData, {
    method: "POST",
  });
}

export async function replaceDish(
  initData: string,
  menu: MenuVariant,
  mealIndex: number,
  hint?: string,
): Promise<MenuVariant> {
  return menuFetch<MenuVariant>("/menus/replace-dish", initData, {
    method: "POST",
    body: JSON.stringify({ menu, meal_index: mealIndex, hint: hint || null }),
  });
}

export async function selectMenu(
  initData: string,
  menu: MenuVariant,
): Promise<SelectedMenu> {
  return menuFetch<SelectedMenu>("/menus/select", initData, {
    method: "POST",
    body: JSON.stringify({ menu }),
  });
}

export async function fetchSelectedMenu(
  initData: string,
): Promise<SelectedMenu | null> {
  const response = await fetch(`${apiUrl}/menus/selected`, {
    headers: { "X-Telegram-Init-Data": initData },
  });

  if (!response.ok) {
    return null;
  }

  const text = await response.text();
  if (!text) {
    return null;
  }

  return JSON.parse(text) as SelectedMenu;
}
