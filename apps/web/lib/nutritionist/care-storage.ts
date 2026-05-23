const STORAGE_KEY = "planam_nutritionist_care";

export type CareToggleId = "water" | "protein" | "menu" | "pantry" | "progress";

export type CareToggles = Record<CareToggleId, boolean>;

const DEFAULT: CareToggles = {
  water: false,
  protein: false,
  menu: true,
  pantry: false,
  progress: false,
};

export function loadCareToggles(): CareToggles {
  if (typeof window === "undefined") {
    return { ...DEFAULT };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT };
    const parsed = JSON.parse(raw) as Partial<CareToggles>;
    return { ...DEFAULT, ...parsed };
  } catch {
    return { ...DEFAULT };
  }
}

export function saveCareToggles(toggles: CareToggles): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toggles));
}
