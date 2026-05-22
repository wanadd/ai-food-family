export type PantryItem = {
  id: number;
  scope_mode: string;
  user_id: number | null;
  family_id: number | null;
  name: string;
  category: string;
  quantity: string;
  unit: string;
  source: string;
  note: string | null;
  expires_at: string | null;
  is_expired: boolean;
  days_until_expiry: number;
  added_by_name: string | null;
  created_at: string;
  updated_at: string;
};

export type PantryList = {
  scope_mode: string;
  user_id: number | null;
  family_id: number | null;
  items: PantryItem[];
  active_count: number;
  expired_count: number;
};

export type PantryItemDraft = {
  name: string;
  category: string;
  quantity: string;
  unit: string;
  expires_at: string;
  note: string;
};

export const EMPTY_PANTRY_DRAFT: PantryItemDraft = {
  name: "",
  category: "продукты",
  quantity: "1",
  unit: "шт",
  expires_at: "",
  note: "",
};

export type PantryFilter =
  | "all"
  | "low"
  | "recent"
  | "shopping"
  | "manual";
