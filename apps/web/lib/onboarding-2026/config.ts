import type { MenuGoalId, PlanModeId } from "@/lib/menu/planner-options";

export const ONBOARDING_TRIAL_DAYS = 3;
export const ONBOARDING_TRIAL_AMS = 50;

export type OnboardingWhoId = "solo" | "couple" | "family" | "sport";
export type OnboardingGoalId =
  | "save_time"
  | "eat_better"
  | "lose_weight"
  | "gain_mass"
  | "for_family";
export type OnboardingRestrictionId = "none" | "allergies" | "diet" | "medical";

export type OnboardingChipOption<T extends string> = {
  id: T;
  label: string;
  hint?: string;
};

export const WHO_OPTIONS: OnboardingChipOption<OnboardingWhoId>[] = [
  { id: "solo", label: "Только я" },
  { id: "couple", label: "Мы вдвоём" },
  { id: "family", label: "Семья" },
  { id: "sport", label: "Спорт" },
];

export const GOAL_OPTIONS: OnboardingChipOption<OnboardingGoalId>[] = [
  { id: "save_time", label: "Экономить время", hint: "Быстрые и простые блюда" },
  { id: "eat_better", label: "Питаться лучше" },
  { id: "lose_weight", label: "Похудеть" },
  { id: "gain_mass", label: "Набрать массу" },
  { id: "for_family", label: "Для семьи" },
];

export const RESTRICTION_OPTIONS: OnboardingChipOption<OnboardingRestrictionId>[] = [
  { id: "none", label: "Нет" },
  { id: "allergies", label: "Аллергии" },
  { id: "diet", label: "Диета" },
  { id: "medical", label: "Заболевания" },
];

export const ALLERGY_CHIPS = [
  "Глютен",
  "Лактоза",
  "Орехи",
  "Яйца",
  "Рыба",
] as const;

export const DIET_CHIPS = [
  "Вегетарианство",
  "Без молочного",
  "Низкоуглеводное",
] as const;

export type OnboardingWizardState = {
  who: OnboardingWhoId | null;
  goal: OnboardingGoalId | null;
  restriction: OnboardingRestrictionId | null;
  allergyTags: string[];
  dietTags: string[];
};

export const INITIAL_WIZARD_STATE: OnboardingWizardState = {
  who: null,
  goal: null,
  restriction: null,
  allergyTags: [],
  dietTags: [],
};

export function mapWhoToPersons(who: OnboardingWhoId): number {
  switch (who) {
    case "couple":
      return 2;
    case "family":
      return 4;
    default:
      return 1;
  }
}

export function mapWizardToNutrition(
  state: OnboardingWizardState,
): { nutrition_goal: MenuGoalId; plan_mode: PlanModeId } {
  let nutrition_goal: MenuGoalId = "healthy";
  let plan_mode: PlanModeId = "healthy";

  if (state.who === "sport") {
    nutrition_goal = "sport";
    plan_mode = "sport";
  }

  switch (state.goal) {
    case "save_time":
      plan_mode = "quick_simple";
      nutrition_goal = "maintain";
      break;
    case "eat_better":
      nutrition_goal = "healthy";
      plan_mode = "healthy";
      break;
    case "lose_weight":
      nutrition_goal = "lose";
      break;
    case "gain_mass":
      nutrition_goal = "gain";
      break;
    case "for_family":
      nutrition_goal = "kids";
      plan_mode = "family";
      break;
    default:
      break;
  }

  if (state.who === "family") {
    plan_mode = "family";
    if (state.goal !== "lose_weight" && state.goal !== "gain_mass") {
      nutrition_goal = "kids";
    }
  }

  return { nutrition_goal, plan_mode };
}

export function mapWizardToProfilePatch(state: OnboardingWizardState) {
  const { nutrition_goal } = mapWizardToNutrition(state);
  const allergies =
    state.restriction === "allergies" ? [...state.allergyTags] : [];
  const diets = state.restriction === "diet" ? [...state.dietTags] : [];
  const medical_restrictions =
    state.restriction === "medical"
      ? "Есть медицинские ограничения — учтём при составлении плана"
      : "";

  return {
    nutrition_goal,
    allergies,
    diets,
    medical_restrictions,
    banned_foods: "",
    disliked_foods: "",
    completed: true,
    activity_level: "moderate",
    cooking_time: state.goal === "save_time" ? "minimal" : "medium",
  };
}
