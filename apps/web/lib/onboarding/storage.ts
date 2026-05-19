import { INITIAL_ONBOARDING, type OnboardingData } from "./types";

const STORAGE_KEY = "aiff-onboarding-v1";

export function loadLocalOnboarding(): OnboardingData {
  if (typeof window === "undefined") {
    return INITIAL_ONBOARDING;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return INITIAL_ONBOARDING;
    }
    const parsed = JSON.parse(raw) as OnboardingData;
    return { ...INITIAL_ONBOARDING, ...parsed };
  } catch {
    return INITIAL_ONBOARDING;
  }
}

export function saveLocalOnboarding(data: OnboardingData): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function clearLocalOnboarding(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
}
