export type FamilyRole = "admin" | "adult" | "child";

export type FamilyMember = {
  id: number;
  family_id: number;
  user_id: number | null;
  display_name: string;
  role: FamilyRole;
  goals: string[];
  restrictions: string[];
  is_you: boolean;
  created_at: string;
  updated_at: string;
};

export type Family = {
  id: number;
  name: string;
  members: FamilyMember[];
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
