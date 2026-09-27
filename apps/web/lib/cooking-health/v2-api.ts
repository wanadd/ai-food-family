import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";
import type { ConsumptionEventV2, CookingSessionV2, HealthProjectionV2 } from "./v2-types";

const mutation = (key: string) => ({ "Idempotency-Key": key });

export const startCookingV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<CookingSessionV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/cooking-sessions`, { method: "POST", headers: mutation(key), body: JSON.stringify(body) });
export const completeCookingV2 = (init: string, mode: AppMode, sessionId: string, body: object, key: string) => apiFetch<CookingSessionV2>(init, mode, `/v2/cooking-sessions/${encodeURIComponent(sessionId)}/complete`, { method: "POST", headers: mutation(key), body: JSON.stringify(body) });
export const recordMealCheckinV2 = (init: string, mode: AppMode, personId: string, body: object, key: string) => apiFetch<ConsumptionEventV2>(init, mode, `/v2/people/${encodeURIComponent(personId)}/meal-checkins`, { method: "POST", headers: mutation(key), body: JSON.stringify(body) });
export const readHealthDeviationsV2 = (init: string, mode: AppMode, personId: string, query = "") => apiFetch<{ person_id: string; projections: HealthProjectionV2[] }>(init, mode, `/v2/people/${encodeURIComponent(personId)}/health/deviations${query}`);
