export type FamilyRole = "admin" | "adult" | "child";
export type MemberType = "telegram" | "virtual";

export type VirtualNutrition = {
  age: number | null;
  nutrition_goal: string | null;
  allergies: string[];
  restrictions: string[];
  diets: string[];
  favorite_foods: string;
  disliked_foods: string;
  notes: string;
};

export type FamilyMember = {
  id: number;
  family_id: number;
  user_id: number | null;
  display_name: string;
  role: FamilyRole;
  goals: string[];
  restrictions: string[];
  is_you: boolean;
  is_virtual: boolean;
  member_type: MemberType;
  role_label: string;
  nutrition_goal_label: string | null;
  nutrition_profile_complete: boolean;
  allow_admin_profile_edit: boolean;
  virtual_kind: string | null;
  can_admin_edit_nutrition: boolean;
  nutrition_summary: Record<string, unknown> | null;
  virtual_nutrition: VirtualNutrition | null;
  created_at: string;
  updated_at: string;
};

export type Family = {
  id: number;
  name: string;
  members: FamilyMember[];
  members_count: number;
  plan_label: string;
  your_role: FamilyRole | null;
  created_at: string;
  updated_at: string;
};

export type MemberDraft = {
  display_name: string;
  role: FamilyRole;
  goals: string[];
  restrictions: string[];
};

export const EMPTY_MEMBER_DRAFT: MemberDraft = {
  display_name: "",
  role: "adult",
  goals: [],
  restrictions: [],
};

export const EMPTY_VIRTUAL_NUTRITION: VirtualNutrition = {
  age: null,
  nutrition_goal: null,
  allergies: [],
  restrictions: [],
  diets: [],
  favorite_foods: "",
  disliked_foods: "",
  notes: "",
};

export type VirtualMemberDraft = {
  display_name: string;
  virtual_kind: string | null;
  role: "adult" | "child";
  nutrition: VirtualNutrition;
};

export const EMPTY_VIRTUAL_DRAFT: VirtualMemberDraft = {
  display_name: "",
  virtual_kind: "child",
  role: "child",
  nutrition: { ...EMPTY_VIRTUAL_NUTRITION },
};
