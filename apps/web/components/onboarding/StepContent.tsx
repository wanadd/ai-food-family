import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { OptionCards } from "@/components/onboarding/OptionCards";
import { TextAreaField } from "@/components/onboarding/TextAreaField";
import {
  ALLERGY_OPTIONS,
  BUDGET_OPTIONS,
  COOKING_TIME_OPTIONS,
  DIET_OPTIONS,
  GOAL_OPTIONS,
  RESTRICTION_OPTIONS,
} from "@/lib/onboarding/options";
import type { OnboardingData, OnboardingStepId } from "@/lib/onboarding/types";

type StepContentProps = {
  stepId: OnboardingStepId;
  data: OnboardingData;
  onChange: (patch: Partial<OnboardingData>) => void;
};

export function StepContent({ stepId, data, onChange }: StepContentProps) {
  switch (stepId) {
    case "welcome":
      return (
        <div className="space-y-4 rounded-2xl border border-dashed border-emerald-200 bg-emerald-50/60 p-5 text-sm leading-relaxed text-stone-600">
          <p>
            Мы подберём меню с учётом целей, диет, аллергий и ваших вкусовых
            предпочтений.
          </p>
          <p>Прогресс сохраняется автоматически — можно вернуться позже.</p>
        </div>
      );

    case "goals":
      return (
        <ChipSelect
          options={GOAL_OPTIONS}
          value={data.goals}
          onChange={(goals) => onChange({ goals })}
        />
      );

    case "diets":
      return (
        <ChipSelect
          options={DIET_OPTIONS}
          value={data.diets}
          onChange={(diets) => onChange({ diets })}
          exclusiveNone="none"
        />
      );

    case "allergies":
      return (
        <ChipSelect
          options={ALLERGY_OPTIONS}
          value={data.allergies}
          onChange={(allergies) => onChange({ allergies })}
          exclusiveNone="none"
        />
      );

    case "restrictions":
      return (
        <ChipSelect
          options={RESTRICTION_OPTIONS}
          value={data.restrictions}
          onChange={(restrictions) => onChange({ restrictions })}
          exclusiveNone="none"
        />
      );

    case "favoriteFoods":
      return (
        <TextAreaField
          value={data.favoriteFoods}
          onChange={(favoriteFoods) => onChange({ favoriteFoods })}
          placeholder="Например: курица, гречка, брокколи, творог…"
        />
      );

    case "dislikedFoods":
      return (
        <TextAreaField
          value={data.dislikedFoods}
          onChange={(dislikedFoods) => onChange({ dislikedFoods })}
          placeholder="Например: печень, сельдерей, капуста…"
        />
      );

    case "budget":
      return (
        <OptionCards
          options={BUDGET_OPTIONS}
          value={data.budget}
          onChange={(budget) => onChange({ budget })}
        />
      );

    case "cookingTime":
      return (
        <OptionCards
          options={COOKING_TIME_OPTIONS}
          value={data.cookingTime}
          onChange={(cookingTime) => onChange({ cookingTime })}
        />
      );

    default:
      return null;
  }
}
