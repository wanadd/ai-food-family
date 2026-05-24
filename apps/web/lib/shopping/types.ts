export type ShoppingCategory = {
  id: number;
  slug: string;
  name: string;
  icon: string | null;
  is_food: boolean;
  is_system: boolean;
  created_at: string;
};

export type ShoppingListItem = {
  id: string;
  name: string;
  category: string;
  quantity: string;
  unit: string;
  amount: string;
  amounts: string[];
  note: string | null;
  source: string;
  checked: boolean;
  checked_by_user_id: number | null;
  checked_by_name: string | null;
  checked_at: string | null;
  linked_pantry_item_id: number | null;
  added_to_pantry: boolean;
  created_by_user_id: number | null;
};

export type ShoppingList = {
  scope_mode: string;
  user_id: number | null;
  family_id: number | null;
  menu_title: string | null;
  items: ShoppingListItem[];
  categories: ShoppingCategory[];
  total_count: number;
  checked_count: number;
  updated_at: string;
};

export type ShoppingItemDraft = {
  name: string;
  category: string;
  quantity: string;
  unit: string;
  note: string;
  is_food: boolean;
};

export const EMPTY_SHOPPING_DRAFT: ShoppingItemDraft = {
  name: "",
  category: "продукты",
  quantity: "1",
  unit: "шт",
  note: "",
  is_food: true,
};
