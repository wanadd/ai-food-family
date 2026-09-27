import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";
import type { PantryReadModelV2, ReceiptProposalV2, ShoppingReadModelV2 } from "./v2-types";

const headers = (key: string) => ({ "Idempotency-Key": key });
export const readShoppingV2 = (init: string, mode: AppMode, householdId: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/shopping`);
export const addShoppingItemV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/shopping/items`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const purchaseShoppingItemV2 = (init: string, mode: AppMode, householdId: string, itemId: string, addToPantry: boolean, key: string) => apiFetch<ShoppingReadModelV2>(init, mode, `/v2/shopping/items/${encodeURIComponent(itemId)}/purchase`, { method: "POST", headers: { ...headers(key), "X-Planam-Household-Id": householdId }, body: JSON.stringify({ add_to_pantry: addToPantry }) });
export const readPantryV2 = (init: string, mode: AppMode, householdId: string) => apiFetch<PantryReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/pantry`);
export const adjustPantryV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<PantryReadModelV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/pantry/adjust`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const createReceiptV2 = (init: string, mode: AppMode, householdId: string, body: object, key: string) => apiFetch<ReceiptProposalV2>(init, mode, `/v2/households/${encodeURIComponent(householdId)}/receipts`, { method: "POST", headers: headers(key), body: JSON.stringify(body) });
export const acceptReceiptV2 = (init: string, mode: AppMode, householdId: string, receiptId: string, proposalId: string, lineIds: string[], key: string) => apiFetch<Record<string, unknown>>(init, mode, `/v2/receipts/${encodeURIComponent(receiptId)}/proposals/${encodeURIComponent(proposalId)}/accept`, { method: "POST", headers: { ...headers(key), "X-Planam-Household-Id": householdId }, body: JSON.stringify({ line_ids: lineIds }) });
