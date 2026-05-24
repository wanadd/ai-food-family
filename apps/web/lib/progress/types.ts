export type MemberProgressStatus =
  | "improving"
  | "stable"
  | "attention"
  | "hidden";

export type NutritionActual = {
  calories_consumed: number;
  protein_consumed_g: number;
  fat_consumed_g: number;
  carbs_consumed_g: number;
  water_consumed_ml: number;
  meals_logged: number;
};

export type NutritionTargets = {
  calories_target: number | null;
  protein_target_g: number | null;
  fat_target_g: number | null;
  carbs_target_g: number | null;
  fiber_target_g: number | null;
  water_target_ml: number | null;
  goal_type: string | null;
};

export type ProgressEntry = {
  id: number;
  weight_kg: number | null;
  body_fat_percent: number | null;
  waist_cm: number | null;
  chest_cm: number | null;
  hips_cm: number | null;
  notes: string | null;
  recorded_at: string;
};

export type TrainingEntry = {
  id: number;
  training_type: string;
  duration_minutes: number | null;
  intensity: string;
  calories_burned: number | null;
  notes: string | null;
  training_date: string;
};

export type FamilyMemberProgress = {
  member_id: number;
  name: string;
  goal_label: string | null;
  progress_summary: string;
  status: MemberProgressStatus;
  is_you: boolean;
};

export type ProgressOverview = {
  is_pro: boolean;
  goal_label: string | null;
  goal_type: string | null;
  current_weight_kg: number | null;
  start_weight_kg?: number | null;
  target_weight_kg?: number | null;
  goal_started_at?: string | null;
  goal_forecast_date?: string | null;
  weight_change_week_kg: number | null;
  goal_progress_percent: number | null;
  targets: NutritionTargets | null;
  daily_actual?: NutritionActual | null;
  trainings_this_week: number;
  training_minutes_week: number;
  show_progress_to_family: boolean;
  family_progress: FamilyMemberProgress[];
  pro_recommendation: string | null;
  latest_entry: ProgressEntry | null;
};

export type ProgressEntryCreate = {
  weight_kg?: number | null;
  waist_cm?: number | null;
  chest_cm?: number | null;
  hips_cm?: number | null;
  notes?: string | null;
};

export type TrainingEntryCreate = {
  training_type: string;
  duration_minutes?: number | null;
  intensity: "low" | "medium" | "high";
  notes?: string | null;
};
