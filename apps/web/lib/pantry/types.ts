export type PantryItem = {
  id: number;
  scope_mode: string;
  user_id: number | null;
  family_id: number | null;
  name: string;
  quantity: string;
  expires_at: string;
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
  quantity: string;
  expires_at: string;
};

export const EMPTY_PANTRY_DRAFT: PantryItemDraft = {
  name: "",
  quantity: "",
  expires_at: "",
};
