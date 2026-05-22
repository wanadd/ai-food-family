export type ShoppingListItem = {
  id: string;
  name: string;
  amount: string;
  amounts: string[];
  category: string;
  checked: boolean;
  checked_by_user_id: number | null;
  checked_by_name: string | null;
  checked_at: string | null;
  linked_pantry_item_id: number | null;
  added_to_pantry: boolean;
};

export type ShoppingList = {
  scope_mode: string;
  user_id: number | null;
  family_id: number | null;
  menu_title: string | null;
  items: ShoppingListItem[];
  total_count: number;
  checked_count: number;
  updated_at: string;
};
