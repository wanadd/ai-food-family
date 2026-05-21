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
};

export type ShoppingList = {
  family_id: number;
  menu_title: string | null;
  items: ShoppingListItem[];
  total_count: number;
  checked_count: number;
  updated_at: string;
};
