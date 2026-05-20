import {
  ALLERGY_OPTIONS,
  GOAL_OPTIONS,
  RESTRICTION_OPTIONS,
} from "@/lib/onboarding/options";

import type { FamilyRole } from "./types";

const ROLE_LABELS: Record<FamilyRole, string> = {
  admin: "Админ",
  adult: "Взрослый",
  child: "Ребёнок",
};

export function roleLabel(role: FamilyRole): string {
  return ROLE_LABELS[role];
}

export function labelsFor(values: string[]) {
  if (!values.length) {
    return "—";
  }

  const all = [...GOAL_OPTIONS, ...RESTRICTION_OPTIONS, ...ALLERGY_OPTIONS];
  return values
    .map((value) => all.find((option) => option.value === value)?.label ?? value)
    .join(", ");
}
