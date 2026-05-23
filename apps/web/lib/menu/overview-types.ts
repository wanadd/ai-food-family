import type { SelectedMenu } from "./types";

export type MenuOverview = {
  plan_summary: {
    goal_label: string;
    persons_label: string;
    plan_mode_label: string;
    estimated_cost_rub: number | null;
    pantry_used_rub: number | null;
    savings_rub: number | null;
    has_selected_menu: boolean;
    menu_title: string | null;
  };
  why_reasons: { text: string; included: boolean }[];
  nutritionist_advice: {
    level: "ok" | "suggest_update" | "update_recommended";
    title: string;
    body: string;
    freshness_status: "current" | "needs_update" | "no_menu";
    update_reason: string | null;
  };
  selected_menu: SelectedMenu | null;
  pro_coverage: {
    protein_percent: number;
    fiber_percent: number;
    calories_percent: number;
    water_percent: number;
  } | null;
  is_pro: boolean;
  persons_count: number;
  plan_mode: string | null;
  meal_leftovers_count: number;
};

export type RecipeEvaluation = {
  fit_level: "good" | "partial" | "not_recommended";
  title: string;
  reasons: { code: string; label: string }[];
};

export type RecipeFamilyFit = {
  members: { member_id: number | null; name: string; status: "ok" | "warning"; note: string }[];
};

export type RecipeImproveSuggestion = {
  id: string;
  label: string;
  description: string;
};
