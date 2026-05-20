import {
  ALLERGY_OPTIONS,
  RESTRICTION_OPTIONS,
  type SelectOption,
} from "@/lib/onboarding/options";

export const MEMBER_RESTRICTION_OPTIONS: SelectOption[] = [
  ...RESTRICTION_OPTIONS,
  ...ALLERGY_OPTIONS.filter((option) => option.value !== "none"),
];
