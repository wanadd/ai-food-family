export type ShoppingState = "NEEDED" | "CHECKED" | "PURCHASED" | "REMOVED" | "DEFERRED";
export type ShoppingItemV2 = { shopping_item_id: string; display_text: string; quantity: number | null; unit: string | null; uncertainty: string; category: string | null; state: ShoppingState; source: string };
export type ShoppingDemandV2 = { demand_id: string; display_text: string; quantity: number | null; unit: string | null; uncertainty: string; source: string; plan_revision_id: string | null; recipe_version_id: string | null };
export type ShoppingReadModelV2 = { shopping_list_id: string; owner_scope: "PERSON" | "HOUSEHOLD"; person_id: string | null; household_id: string | null; demands: ShoppingDemandV2[]; items: ShoppingItemV2[] };
export type PantryItemV2 = { pantry_inventory_id: string; display_text: string; quantity: number | null; unit: string | null; uncertainty: string; lot_code: string | null; expiry_date: string | null };
export type PantryReadModelV2 = { owner_scope: "PERSON" | "HOUSEHOLD"; person_id: string | null; household_id: string | null; items: PantryItemV2[] };
export type ReceiptProposalV2 = { receipt_document_id: string; receipt_proposal_id: string; state: string };
