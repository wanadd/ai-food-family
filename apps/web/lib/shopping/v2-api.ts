import { apiFetch } from "@/lib/api-client";
import { buildApiUrl, getApiBaseUrl } from "@/lib/api-base";
import { buildProtectedRequestHeaders } from "@/lib/audit/audit-mode";
import type { AppMode } from "@/lib/app-mode/types";
import type { PantryReadModelV2, ReceiptProposalV2, ShoppingReadModelV2 } from "./v2-types";
import type { ShoppingList, ShoppingListItem } from "./types";
import type { PantryList, PantryItem, PantryItemDraft } from "@/lib/pantry/types";

const headers = (key: string) => ({ "Idempotency-Key": key });

type V2Session = { access_token: string; person_id?: string | null };
type V2Scope = { personId: string | null; householdId: string | null };
const sessionPromises = new Map<string, Promise<V2Session>>();
const scopePromises = new Map<string, Promise<V2Scope>>();

function canonicalV2Path(path: string): string {
  const apiPrefix = getApiBaseUrl().replace(/\/+$/, "").endsWith("/api") ? "" : "/api";
  return `${apiPrefix}${path}`;
}

async function readJson<T>(response: Response): Promise<T> {
  const body = (await response.json().catch(() => ({}))) as { error?: { message?: string } };
  if (!response.ok) throw new Error(body.error?.message ?? `HTTP ${response.status}`);
  return body as T;
}

async function session(init: string): Promise<V2Session> {
  let sessionPromise = sessionPromises.get(init);
  if (!sessionPromise) {
    sessionPromise = fetch(buildApiUrl(canonicalV2Path("/v2/auth/bootstrap")), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...buildProtectedRequestHeaders(init) },
      body: JSON.stringify({ provider: "telegram", init_data: init, client_type: "web" }),
    }).then((response) => readJson<V2Session>(response));
    sessionPromises.set(init, sessionPromise);
  }
  return sessionPromise;
}

async function v2Fetch<T>(init: string, path: string, options: RequestInit = {}): Promise<T> {
  const issued = await session(init);
  const response = await fetch(buildApiUrl(canonicalV2Path(path)), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Planam-Session": issued.access_token,
      ...options.headers,
    },
  });
  return readJson<T>(response);
}

async function scope(init: string, mode: AppMode): Promise<V2Scope> {
  let scopePromise = scopePromises.get(init);
  if (!scopePromise) {
    scopePromise = Promise.all([
      session(init),
      v2Fetch<{ person_id: string | null }>(init, "/v2/me"),
      v2Fetch<Array<{ household_id: string }>>(init, "/v2/households"),
    ]).then(([, me, households]) => ({
      personId: me.person_id,
      householdId: mode === "family" ? households[0]?.household_id ?? null : null,
    }));
    scopePromises.set(init, scopePromise);
  }
  const resolved = await scopePromise;
  return mode === "family" && resolved.householdId
    ? resolved
    : { personId: resolved.personId, householdId: null };
}

function ownerPath(scopeValue: V2Scope, suffix: string): string {
  if (scopeValue.householdId) return `/v2/households/${encodeURIComponent(scopeValue.householdId)}${suffix}`;
  if (scopeValue.personId) return `/v2/persons/${encodeURIComponent(scopeValue.personId)}${suffix}`;
  throw new Error("V2 person scope is unavailable");
}

function mapShopping(data: ShoppingReadModelV2): ShoppingList {
  const items: ShoppingListItem[] = data.items.map((item) => ({
    id: item.shopping_item_id,
    name: item.display_text,
    category: item.category ?? "другое",
    quantity: item.quantity == null ? "" : String(item.quantity),
    unit: item.unit ?? "",
    amount: item.quantity == null ? "" : String(item.quantity),
    amounts: [],
    note: null,
    source: item.source,
    checked: item.state !== "NEEDED",
    checked_by_user_id: null,
    checked_by_name: null,
    checked_at: null,
    linked_pantry_item_id: null,
    added_to_pantry: item.state === "PURCHASED",
    created_by_user_id: null,
  }));
  return {
    scope_mode: data.owner_scope,
    user_id: null,
    family_id: null,
    menu_title: null,
    items,
    categories: [],
    total_count: items.length,
    checked_count: items.filter((item) => item.checked).length,
    updated_at: new Date().toISOString(),
  };
}

function mapPantry(data: PantryReadModelV2): PantryList {
  const items: PantryItem[] = data.items.map((item) => ({
    id: item.pantry_inventory_id,
    scope_mode: data.owner_scope,
    user_id: null,
    family_id: null,
    name: item.display_text,
    category: "другое",
    quantity: item.quantity == null ? "" : String(item.quantity),
    unit: item.unit ?? "",
    source: "v2",
    note: null,
    expires_at: item.expiry_date,
    is_expired: false,
    days_until_expiry: 999,
    added_by_name: null,
    created_at: "",
    updated_at: "",
  }));
  return { scope_mode: data.owner_scope, user_id: null, family_id: null, items, active_count: items.length, expired_count: 0 };
}

export async function fetchShoppingV2(init: string, mode: AppMode): Promise<ShoppingList> {
  const active = await scope(init, mode);
  return mapShopping(await v2Fetch<ShoppingReadModelV2>(init, ownerPath(active, "/shopping")));
}

export async function addShoppingItemV2Compat(init: string, mode: AppMode, draft: { name: string; quantity: string; unit: string; category: string }, key: string): Promise<ShoppingList> {
  const active = await scope(init, mode);
  const data = await v2Fetch<ShoppingReadModelV2>(init, ownerPath(active, "/shopping/items"), { method: "POST", headers: headers(key), body: JSON.stringify({ display_text: draft.name, quantity: Number(draft.quantity) || null, unit: draft.unit || null, category: draft.category }) });
  return mapShopping(data);
}

export async function purchaseShoppingItemV2Compat(init: string, mode: AppMode, itemId: string, addToPantry: boolean, key: string): Promise<ShoppingList> {
  const data = await v2Fetch<ShoppingReadModelV2>(init, `/v2/shopping/items/${encodeURIComponent(itemId)}/purchase`, { method: "POST", headers: headers(key), body: JSON.stringify({ add_to_pantry: addToPantry }) });
  return mapShopping(data);
}

export async function deleteShoppingItemV2Compat(init: string, mode: AppMode, itemId: string, key: string): Promise<ShoppingList> {
  const data = await v2Fetch<ShoppingReadModelV2>(init, `/v2/shopping/items/${encodeURIComponent(itemId)}`, { method: "DELETE", headers: headers(key) });
  return mapShopping(data);
}

export async function fetchPantryV2(init: string, mode: AppMode): Promise<PantryList> {
  const active = await scope(init, mode);
  return mapPantry(await v2Fetch<PantryReadModelV2>(init, ownerPath(active, "/pantry")));
}

export async function addPantryItemV2Compat(init: string, mode: AppMode, draft: PantryItemDraft, key: string): Promise<PantryList> {
  const active = await scope(init, mode);
  return mapPantry(await v2Fetch<PantryReadModelV2>(init, ownerPath(active, "/pantry/adjust"), { method: "POST", headers: headers(key), body: JSON.stringify({ display_text: draft.name, quantity_delta: Number(draft.quantity) || null, unit: draft.unit || null }) }));
}

export async function deletePantryItemV2Compat(init: string, mode: AppMode, item: PantryItem, key: string): Promise<PantryList> {
  const active = await scope(init, mode);
  return mapPantry(await v2Fetch<PantryReadModelV2>(init, ownerPath(active, "/pantry/adjust"), { method: "POST", headers: headers(key), body: JSON.stringify({ display_text: item.name, quantity_delta: -(Number(item.quantity) || 0), unit: item.unit || null }) }));
}

export const readShoppingV2 = (init: string, mode: AppMode, householdId: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/shopping`);
export const addShoppingItemV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/shopping/items`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const purchaseShoppingItemV2 = (init: string, mode: AppMode, householdId: string, itemId: string, addToPantry: boolean, key: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/shopping/items/${encodeURIComponent(itemId)}/purchase`, { method: "POST", headers: { ...headers(key), "X-Planam-Household-Id": householdId }, body: JSON.stringify({ add_to_pantry: addToPantry }) });
export const readPantryV2 = (init: string, mode: AppMode, householdId: string) => apiFetch<PantryReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/pantry`);
export const adjustPantryV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<PantryReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/pantry/adjust`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const createReceiptV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<ReceiptProposalV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/receipts`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const acceptReceiptV2 = (init: string, mode: AppMode, householdId: string, receiptId: string, proposalId: string, lineIds: string[], key: string) => apiFetch<Record<string, unknown>>(init, mode, `/v2/receipts/${encodeURIComponent(receiptId)}/proposals/${encodeURIComponent(proposalId)}/accept`, { method: "POST", headers: { ...headers(key), "X-Planam-Household-Id": householdId }, body: JSON.stringify({ line_ids: lineIds }) });
