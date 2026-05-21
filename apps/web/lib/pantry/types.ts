export type PantryItem = {
  id: number;
  family_id: number;
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
  family_id: number;
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
