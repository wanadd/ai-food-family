import { apiUrl } from "@/lib/api";

export type EventPlanCreatePayload = {
  event_type: string;
  title?: string;
  guests_count: number;
  budget?: string;
  theme?: string;
  cuisine?: string;
  religious_restriction?: string;
  fasting_mode?: string;
  drink_menu_mode?: string;
  alcohol_enabled?: boolean;
  kids_drinks_enabled?: boolean;
  allergies_note?: string;
};

export type EventPlanDetail = {
  id: number;
  title: string;
  event_type: string;
  guests_count: number;
  status: string;
  dishes: { recipe_id: number; title: string; meal_type: string; servings: number }[];
  shopping: { name: string; amount: string; category?: string; from_pantry?: boolean }[];
  nutrition_note?: string;
  estimated_cost_rub?: number;
  created_at: string;
};

async function eventFetch<T>(
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

export async function createEventPlan(
  initData: string,
  payload: EventPlanCreatePayload,
): Promise<EventPlanDetail> {
  return eventFetch<EventPlanDetail>("/event-plans", initData, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createEventShoppingList(
  initData: string,
  planId: number,
): Promise<void> {
  await eventFetch<void>(`/event-plans/${planId}/create-shopping-list`, initData, {
    method: "POST",
  });
}
