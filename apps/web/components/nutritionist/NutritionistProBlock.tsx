"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchProgressOverview } from "@/lib/progress/api";
import { formatWeightDelta, formatWeightKg } from "@/lib/progress/labels";
import type { ProgressOverview } from "@/lib/progress/types";

type NutritionistProBlockProps = {
  goalLabel: string | null;
};

export function NutritionistProBlock({ goalLabel }: NutritionistProBlockProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [progress, setProgress] = useState<ProgressOverview | null>(null);

  const load = useCallback(async () => {
    if (!initData) return;
    try {
      const data = await fetchProgressOverview(initData, mode);
      setProgress(data);
    } catch {
      setProgress(null);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!progress) {
    return null;
  }

  if (!progress.is_pro) {
    return (
      <section className="rounded-2xl border border-stone-200 bg-stone-50/90 p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-sm font-bold text-stone-900">PRO-рекомендации</p>
            <p className="mt-1 text-sm text-stone-600">
              {goalLabel
                ? `Цель: ${goalLabel}. Расширенный прогресс — в ПланАм PRO.`
                : "Прогресс, спорт и аналитика доступны в ПланАм PRO"}
            </p>
          </div>
          <span className="rounded-full bg-stone-200 px-2 py-0.5 text-[10px] font-bold uppercase text-stone-600">
            PRO
          </span>
        </div>
        <Link
          href="/subscription"
          className="mt-3 flex min-h-[40px] items-center justify-center rounded-xl border border-stone-300 bg-white text-sm font-semibold text-stone-800"
        >
          Узнать о PRO
        </Link>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/80 to-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-bold text-stone-900">PRO-рекомендации</p>
        <Link
          href="/progress"
          className="text-xs font-semibold text-emerald-700"
        >
          Прогресс →
        </Link>
      </div>
      <p className="mt-2 text-sm text-stone-700">
        <span className="font-semibold">Цель:</span>{" "}
        {progress.goal_label ?? goalLabel ?? "Не задана"}
      </p>
      <div className="mt-2 flex flex-wrap gap-3 text-sm text-stone-600">
        <span>Вес: {formatWeightKg(progress.current_weight_kg)}</span>
        <span>Неделя: {formatWeightDelta(progress.weight_change_week_kg)}</span>
        {progress.goal_progress_percent != null ? (
          <span>Прогресс: {progress.goal_progress_percent}%</span>
        ) : null}
      </div>
      {progress.pro_recommendation ? (
        <p className="mt-3 rounded-xl bg-white/80 p-3 text-sm leading-relaxed text-stone-800">
          {progress.pro_recommendation}
        </p>
      ) : null}
      <p className="mt-2 text-xs text-stone-500">
        Тренировок за неделю: {progress.trainings_this_week}
      </p>
    </section>
  );
}
