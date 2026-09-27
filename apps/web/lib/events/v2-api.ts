import { apiFetch } from "@/lib/api-client";
import { buildApiUrl } from "@/lib/api-base";
import type { EventCollection, EventInvitation, EventMenu, EventReadModel, EventShopping } from "./v2-types";
import type { AppMode } from "@/lib/app-mode/types";

const key = () => `web-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
const headers = (idempotencyKey: string) => ({ "Idempotency-Key": idempotencyKey });

export function listEvents(initData: string, mode: AppMode) {
  return apiFetch<EventCollection>(initData, mode, "/v2/events");
}

export function getEvent(initData: string, mode: AppMode, eventId: string) {
  return apiFetch<EventReadModel>(initData, mode, `/v2/events/${encodeURIComponent(eventId)}`);
}

export function createEvent(initData: string, mode: AppMode, body: { title: string; event_type: string; starts_at: string; collaboration_mode: string }) {
  return apiFetch<EventReadModel>(initData, mode, "/v2/events", { method: "POST", headers: headers(key()), body: JSON.stringify(body) });
}

export function transitionEvent(initData: string, mode: AppMode, eventId: string, expectedVersion: number, status: string) {
  return apiFetch<EventReadModel>(initData, mode, `/v2/events/${encodeURIComponent(eventId)}/lifecycle`, { method: "POST", headers: headers(key()), body: JSON.stringify({ expected_version: expectedVersion, status }) });
}

export function createEventInvitation(initData: string, mode: AppMode, eventId: string) {
  return apiFetch<EventInvitation>(initData, mode, `/v2/events/${encodeURIComponent(eventId)}/invitations`, { method: "POST", headers: headers(key()), body: JSON.stringify({}) });
}

export function getEventMenu(initData: string, mode: AppMode, eventId: string) {
  return apiFetch<EventMenu>(initData, mode, `/v2/events/${encodeURIComponent(eventId)}/menu`);
}

export function getEventShopping(initData: string, mode: AppMode, eventId: string) {
  return apiFetch<EventShopping>(initData, mode, `/v2/events/${encodeURIComponent(eventId)}/shopping`);
}

export function inspectEventInvitation(token: string) {
  return fetch(`${buildApiUrl(`/v2/event-invitations/inspect?token=${encodeURIComponent(token)}`)}`).then(async (response) => {
    if (!response.ok) throw new Error("Приглашение недействительно или устарело");
    return (await response.json()) as { invitation_id: string; event_id: string; title: string; starts_at: string; status: string; expires_at: string | null };
  });
}

export function respondEventInvitation(token: string, participants: Array<{ display_name: string; age_group: string; knowledge_state: string; restrictions: Array<Record<string, unknown>> }>) {
  return fetch(`${buildApiUrl(`/v2/event-invitations/respond?token=${encodeURIComponent(token)}`)}`, { method: "POST", headers: { "Content-Type": "application/json", ...headers(key()) }, body: JSON.stringify({ participants }) }).then(async (response) => {
    if (!response.ok) throw new Error("Не удалось отправить ответ");
    return response.json() as Promise<{ invitation_id: string; participants: unknown[] }>;
  });
}
