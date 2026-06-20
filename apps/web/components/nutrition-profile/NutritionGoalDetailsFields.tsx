"use client";

import { NumberInput } from "@/components/nutrition-profile/NumberInput";
import { OptionCards } from "@/components/onboarding/OptionCards";
import type { NutritionGoalDetails, NutritionProfileData } from "@/lib/nutrition-profile/types";

const PACE_OPTIONS = [
  { value: "soft", label: "Мягкий" },
  { value: "standard", label: "Стандартный" },
  { value: "intensive", label: "Интенсивный" },
];

const GAIN_TYPE_OPTIONS = [
  { value: "muscle", label: "Мышечная масса" },
  { value: "general", label: "Общий набор" },
];

const SPORT_GOAL_OPTIONS = [
  { value: "strength", label: "Сила" },
  { value: "endurance", label: "Выносливость" },
  { value: "cut", label: "Сушка" },
  { value: "muscle", label: "Набор мышц" },
  { value: "recovery", label: "Восстановление" },
];

const HEALTH_FOCUS_OPTIONS = [
  { value: "vegetables", label: "Больше овощей" },
  { value: "less_sugar", label: "Меньше сахара" },
  { value: "gut", label: "ЖКТ" },
  { value: "energy", label: "Энергия" },
  { value: "balance", label: "Баланс" },
];

type Props = {
  goal: string | null;
  details: NutritionGoalDetails;
  profile: NutritionProfileData;
  onChange: (details: NutritionGoalDetails) => void;
  onProfilePatch: (partial: Partial<NutritionProfileData>) => void;
};

export function NutritionGoalDetailsFields({
  goal,
  details,
  profile,
  onChange,
  onProfilePatch,
}: Props) {
  const patch = (partial: Partial<NutritionGoalDetails>) =>
    onChange({ ...details, ...partial });

  if (!goal) return null;

  if (goal === "lose" || goal === "gain") {
    return (
      <div className="mt-4 space-y-3 border-t border-cream-border pt-4">
        <NumberInput
          label="Текущий вес, кг"
          value={details.current_weight_kg ?? profile.weight_kg}
          onChange={(v) => {
            patch({ current_weight_kg: v });
            if (v != null) onProfilePatch({ weight_kg: v });
          }}
        />
        <NumberInput
          label="Целевой вес, кг"
          value={details.target_weight_kg ?? null}
          onChange={(v) => patch({ target_weight_kg: v })}
        />
        <label className="block text-sm font-medium text-graphite-700">
          Дата цели
        </label>
        <input
          type="date"
          value={details.target_date ?? ""}
          onChange={(e) => patch({ target_date: e.target.value || null })}
          className="w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
        />
        <p className="text-sm font-medium text-graphite-700">Темп</p>
        <OptionCards
          options={PACE_OPTIONS}
          value={details.goal_pace ?? null}
          onChange={(v) => patch({ goal_pace: v })}
        />
        {goal === "gain" ? (
          <>
            <p className="text-sm font-medium text-graphite-700">Тип набора</p>
            <OptionCards
              options={GAIN_TYPE_OPTIONS}
              value={details.mass_gain_type ?? null}
              onChange={(v) => patch({ mass_gain_type: v })}
            />
            <NumberInput
              label="Тренировок в неделю"
              value={details.workouts_per_week ?? null}
              onChange={(v) => patch({ workouts_per_week: v })}
            />
          </>
        ) : null}
      </div>
    );
  }

  if (goal === "maintain") {
    return (
      <div className="mt-4 space-y-3 border-t border-cream-border pt-4">
        <NumberInput
          label="Текущий вес, кг"
          value={details.current_weight_kg ?? profile.weight_kg}
          onChange={(v) => {
            patch({ current_weight_kg: v });
            if (v != null) onProfilePatch({ weight_kg: v });
          }}
        />
        <NumberInput
          label="Вес от, кг"
          value={details.target_weight_min_kg ?? null}
          onChange={(v) => patch({ target_weight_min_kg: v })}
        />
        <NumberInput
          label="Вес до, кг"
          value={details.target_weight_max_kg ?? null}
          onChange={(v) => patch({ target_weight_max_kg: v })}
        />
      </div>
    );
  }

  if (goal === "sport") {
    return (
      <div className="mt-4 space-y-3 border-t border-cream-border pt-4">
        <p className="text-sm font-medium text-graphite-700">Спортивная цель</p>
        <OptionCards
          options={SPORT_GOAL_OPTIONS}
          value={details.sport_goal_type ?? null}
          onChange={(v) => patch({ sport_goal_type: v })}
        />
        <NumberInput
          label="Тренировок в неделю"
          value={details.workouts_per_week ?? null}
          onChange={(v) => patch({ workouts_per_week: v })}
        />
        <NumberInput
          label="Белок, г/кг"
          value={details.protein_per_kg ?? null}
          onChange={(v) => patch({ protein_per_kg: v })}
        />
        <NumberInput
          label="Вода, мл"
          value={details.water_target_ml ?? null}
          onChange={(v) => patch({ water_target_ml: v })}
        />
      </div>
    );
  }

  if (goal === "healthy") {
    return (
      <div className="mt-4 space-y-3 border-t border-cream-border pt-4">
        <p className="text-sm font-medium text-graphite-700">Фокус</p>
        <OptionCards
          options={HEALTH_FOCUS_OPTIONS}
          value={details.health_focus ?? null}
          onChange={(v) => patch({ health_focus: v })}
        />
      </div>
    );
  }

  return null;
}
