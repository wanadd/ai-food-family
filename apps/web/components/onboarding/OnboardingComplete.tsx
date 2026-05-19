import Link from "next/link";

import type { OnboardingData } from "@/lib/onboarding/types";
import {
  ALLERGY_OPTIONS,
  BUDGET_OPTIONS,
  COOKING_TIME_OPTIONS,
  DIET_OPTIONS,
  GOAL_OPTIONS,
  RESTRICTION_OPTIONS,
} from "@/lib/onboarding/options";

function labelsFor(values: string[], options: { value: string; label: string }[]) {
  if (!values.length) {
    return "—";
  }
  return values
    .map((value) => options.find((option) => option.value === value)?.label ?? value)
    .join(", ");
}

type OnboardingCompleteProps = {
  data: OnboardingData;
};

export function OnboardingComplete({ data }: OnboardingCompleteProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
          Готово
        </p>
        <h2 className="mt-2 text-2xl font-bold text-stone-900">
          Профиль настроен
        </h2>
        <p className="mt-2 text-sm text-stone-600">
          Теперь AI Food Family может подбирать меню под ваши предпочтения.
        </p>
      </div>

      <dl className="space-y-3 text-sm">
        <SummaryRow label="Цели" value={labelsFor(data.goals, GOAL_OPTIONS)} />
        <SummaryRow label="Диеты" value={labelsFor(data.diets, DIET_OPTIONS)} />
        <SummaryRow
          label="Аллергии"
          value={labelsFor(data.allergies, ALLERGY_OPTIONS)}
        />
        <SummaryRow
          label="Ограничения"
          value={labelsFor(data.restrictions, RESTRICTION_OPTIONS)}
        />
        <SummaryRow
          label="Любимое"
          value={data.favoriteFoods.trim() || "—"}
        />
        <SummaryRow
          label="Нелюбимое"
          value={data.dislikedFoods.trim() || "—"}
        />
        <SummaryRow
          label="Бюджет"
          value={
            BUDGET_OPTIONS.find((option) => option.value === data.budget)?.label ??
            "—"
          }
        />
        <SummaryRow
          label="Время готовки"
          value={
            COOKING_TIME_OPTIONS.find(
              (option) => option.value === data.cookingTime,
            )?.label ?? "—"
          }
        />
      </dl>

      <Link
        href="/"
        className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
      >
        На главную
      </Link>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-stone-100 bg-stone-50 px-4 py-3">
      <dt className="text-xs uppercase tracking-wide text-stone-500">{label}</dt>
      <dd className="mt-1 font-medium text-stone-800">{value}</dd>
    </div>
  );
}
