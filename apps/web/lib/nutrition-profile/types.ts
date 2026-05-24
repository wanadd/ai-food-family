export type NutritionGoalDetails = {
  goal_type?: string | null;
  current_weight_kg?: number | null;
  target_weight_kg?: number | null;
  target_weight_min_kg?: number | null;
  target_weight_max_kg?: number | null;
  target_date?: string | null;
  goal_pace?: string | null;
  mass_gain_type?: string | null;
  sport_goal_type?: string | null;
  workouts_per_week?: number | null;
  workout_days?: string[];
  protein_target_g?: number | null;
  protein_per_kg?: number | null;
  water_target_ml?: number | null;
  health_focus?: string | null;
  habit_focus?: string | null;
  child_age_months?: number | null;
  child_feeding_stage?: string | null;
  parent_notes?: string | null;
};

export const EMPTY_GOAL_DETAILS: NutritionGoalDetails = {};

export type NutritionProData = {
  workouts_enabled: boolean;
  workout_goal: string;
  workout_frequency: string | null;
  body_measurements: string;
  water_liters: number | null;
  track_macros: boolean;
};

export type NutritionProfileData = {
  age: number | null;
  gender: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  nutrition_goal: string | null;
  activity_level: string | null;
  allergies: string[];
  medical_restrictions: string;
  banned_foods: string;
  diets: string[];
  favorite_foods: string;
  disliked_foods: string;
  budget: string | null;
  cooking_time: string | null;
  dish_complexity: string | null;
  pro: NutritionProData;
  goal_details: NutritionGoalDetails;
  completed: boolean;
};

export const INITIAL_NUTRITION_PROFILE: NutritionProfileData = {
  age: null,
  gender: null,
  height_cm: null,
  weight_kg: null,
  nutrition_goal: null,
  activity_level: null,
  allergies: [],
  medical_restrictions: "",
  banned_foods: "",
  diets: [],
  favorite_foods: "",
  disliked_foods: "",
  budget: null,
  cooking_time: null,
  dish_complexity: null,
  goal_details: {},
  pro: {
    workouts_enabled: false,
    workout_goal: "",
    workout_frequency: null,
    body_measurements: "",
    water_liters: null,
    track_macros: false,
  },
  completed: false,
};
