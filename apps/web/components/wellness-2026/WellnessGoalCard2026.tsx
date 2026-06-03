import Link from "next/link";

import type { GoalProgressCard } from "@/lib/nutritionist/goal-progress";

type WellnessGoalCard2026Props = {
  goalLabel: string;
  goalCard: GoalProgressCard;
  profileComplete: boolean;
};

export function WellnessGoalCard2026({
  goalLabel,
  goalCard,
  profileComplete,
}: WellnessGoalCard2026Props) {
  if (!profileComplete) {
    return (
      <section className="rounded-card border border-dashed border-pa-border bg-pa-surface p-4">
        <h2 className="pa26-section-title">Цель</h2>
        <p className="pa26-body mt-2 text-pa-muted">
          Укажите цель питания — подстроим меню и подсказки под вас.
        </p>
        <Link
          href="/profile/nutrition"
          className="mt-4 flex min-h-[44px] w-full items-center justify-center rounded-control border border-sage-200 bg-pa-surface px-6 text-[15px] font-semibold text-sage-700 active:scale-[0.99] dark:border-pa-border dark:bg-pa-elevated dark:text-sage-300"
        >
          Настроить питание
        </Link>
      </section>
    );
  }

  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="pa26-micro text-pa-muted">Ваша цель</p>
          <h2 className="pa26-card-title mt-0.5">{goalLabel}</h2>
        </div>
        {goalCard.percent != null ? (
          <span className="shrink-0 rounded-pill bg-sage-100 px-2.5 py-1 pa26-micro font-semibold text-sage-800 dark:bg-sage-700/40 dark:text-sage-200">
            {goalCard.percent}%
          </span>
        ) : null}
      </div>
      {goalCard.remaining ? (
        <p className="pa26-caption mt-2 text-pa-muted">
          До цели: {goalCard.remaining}
        </p>
      ) : null}
      {goalCard.paceLine ? (
        <p className="pa26-caption mt-1 text-pa-muted">{goalCard.paceLine}</p>
      ) : null}
      <Link
        href="/profile/nutrition"
        className="mt-3 inline-block pa26-micro font-semibold text-sage-700 dark:text-sage-300"
      >
        Изменить цель →
      </Link>
    </section>
  );
}
