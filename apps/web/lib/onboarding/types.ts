export type OnboardingData = {
  currentStep: number;
  completed: boolean;
  goals: string[];
  diets: string[];
  allergies: string[];
  restrictions: string[];
  favoriteFoods: string;
  dislikedFoods: string;
  budget: string | null;
  cookingTime: string | null;
};

export const INITIAL_ONBOARDING: OnboardingData = {
  currentStep: 0,
  completed: false,
  goals: [],
  diets: [],
  allergies: [],
  restrictions: [],
  favoriteFoods: "",
  dislikedFoods: "",
  budget: null,
  cookingTime: null,
};

export type OnboardingStepId =
  | "welcome"
  | "goals"
  | "diets"
  | "allergies"
  | "restrictions"
  | "favoriteFoods"
  | "dislikedFoods"
  | "budget"
  | "cookingTime";

export type OnboardingStep = {
  id: OnboardingStepId;
  title: string;
  subtitle: string;
};
