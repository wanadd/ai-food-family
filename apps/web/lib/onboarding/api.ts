import { apiUrl } from "@/lib/api";

import type { OnboardingData } from "./types";

type ApiOnboarding = {
  current_step: number;
  completed: boolean;
  goals: string[];
  diets: string[];
  allergies: string[];
  restrictions: string[];
  favorite_foods: string;
  disliked_foods: string;
  budget: string | null;
  cooking_time: string | null;
};

function toApi(data: OnboardingData): ApiOnboarding {
  return {
    current_step: data.currentStep,
    completed: data.completed,
    goals: data.goals,
    diets: data.diets,
    allergies: data.allergies,
    restrictions: data.restrictions,
    favorite_foods: data.favoriteFoods,
    disliked_foods: data.dislikedFoods,
    budget: data.budget,
    cooking_time: data.cookingTime,
  };
}

function fromApi(payload: ApiOnboarding): OnboardingData {
  return {
    currentStep: payload.current_step,
    completed: payload.completed,
    goals: payload.goals ?? [],
    diets: payload.diets ?? [],
    allergies: payload.allergies ?? [],
    restrictions: payload.restrictions ?? [],
    favoriteFoods: payload.favorite_foods ?? "",
    dislikedFoods: payload.disliked_foods ?? "",
    budget: payload.budget,
    cookingTime: payload.cooking_time,
  };
}

export async function fetchRemoteOnboarding(
  initData: string,
): Promise<OnboardingData | null> {
  const response = await fetch(`${apiUrl}/onboarding/me`, {
    headers: { "X-Telegram-Init-Data": initData },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    return null;
  }

  const payload = (await response.json()) as ApiOnboarding;
  return fromApi(payload);
}

export async function saveRemoteOnboarding(
  initData: string,
  data: OnboardingData,
): Promise<void> {
  const response = await fetch(`${apiUrl}/onboarding/me`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
    },
    body: JSON.stringify(toApi(data)),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }
}
