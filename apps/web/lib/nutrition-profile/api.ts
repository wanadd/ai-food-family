import { apiUrl } from "@/lib/api";

import type { NutritionProfileData } from "./types";

type ApiNutritionProfile = {
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
  pro: NutritionProfileData["pro"];
  completed: boolean;
};

function toApi(data: NutritionProfileData): ApiNutritionProfile {
  return {
    age: data.age,
    gender: data.gender,
    height_cm: data.height_cm,
    weight_kg: data.weight_kg,
    nutrition_goal: data.nutrition_goal,
    activity_level: data.activity_level,
    allergies: data.allergies,
    medical_restrictions: data.medical_restrictions,
    banned_foods: data.banned_foods,
    diets: data.diets,
    favorite_foods: data.favorite_foods,
    disliked_foods: data.disliked_foods,
    budget: data.budget,
    cooking_time: data.cooking_time,
    dish_complexity: data.dish_complexity,
    pro: data.pro,
    completed: data.completed,
  };
}

function fromApi(payload: ApiNutritionProfile): NutritionProfileData {
  return {
    age: payload.age,
    gender: payload.gender,
    height_cm: payload.height_cm,
    weight_kg: payload.weight_kg,
    nutrition_goal: payload.nutrition_goal,
    activity_level: payload.activity_level,
    allergies: payload.allergies ?? [],
    medical_restrictions: payload.medical_restrictions ?? "",
    banned_foods: payload.banned_foods ?? "",
    diets: payload.diets ?? [],
    favorite_foods: payload.favorite_foods ?? "",
    disliked_foods: payload.disliked_foods ?? "",
    budget: payload.budget,
    cooking_time: payload.cooking_time,
    dish_complexity: payload.dish_complexity,
    pro: payload.pro ?? {
      workouts_enabled: false,
      workout_goal: "",
      workout_frequency: null,
      body_measurements: "",
      water_liters: null,
      track_macros: false,
    },
    completed: payload.completed ?? false,
  };
}

export async function fetchNutritionProfile(
  initData: string,
): Promise<NutritionProfileData> {
  const response = await fetch(`${apiUrl}/nutrition-profile/me`, {
    headers: { "X-Telegram-Init-Data": initData },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const payload = (await response.json()) as ApiNutritionProfile;
  return fromApi(payload);
}

export async function saveNutritionProfile(
  initData: string,
  data: NutritionProfileData,
): Promise<NutritionProfileData> {
  const response = await fetch(`${apiUrl}/nutrition-profile/me`, {
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

  const payload = (await response.json()) as ApiNutritionProfile;
  return fromApi(payload);
}
