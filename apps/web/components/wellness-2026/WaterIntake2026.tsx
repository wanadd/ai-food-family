"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { V2ProgressBar } from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { cn } from "@/lib/planam/cn";
import { addWaterIntake, fetchWaterToday } from "@/lib/water-intake/api";

const GLASS_ML = 250;
const DEFAULT_TARGET_ML = 2000;

type WaterIntake2026Props = {
  onUpdated?: () => void;
  compact?: boolean;
};

export function WaterIntake2026({
  onUpdated,
  compact = false,
}: WaterIntake2026Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [total, setTotal] = useState(0);
  const [target, setTarget] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      return;
    }
    try {
      const data = await fetchWaterToday(initData, mode);
      setTotal(data.total_ml);
      setTarget(data.target_ml);
      setError(null);
    } catch {
      setError("Не удалось обновить воду — попробуйте ещё раз");
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addWater(amountMl: number) {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    setFeedback(null);
    try {
      const data = await addWaterIntake(initData, mode, amountMl);
      setTotal(data.total_ml);
      setTarget(data.target_ml);
      invalidateCache("progress-overview");
      setFeedback(`Добавили ${amountMl} мл`);
      onUpdated?.();
      window.setTimeout(() => setFeedback(null), 2500);
    } catch {
      setError("Не удалось добавить воду — данные дня сохранены");
    } finally {
      setSaving(false);
    }
  }

  const effectiveTarget = target ?? DEFAULT_TARGET_ML;
  const hasExplicitTarget = target != null && target > 0;
  const pct =
    hasExplicitTarget && effectiveTarget > 0
      ? Math.min(100, Math.round((total / effectiveTarget) * 100))
      : null;

  if (compact) {
    return (
      <section
        className="rounded-card border border-blue-200/60 bg-blue-50/40 px-3 py-3 dark:border-blue-900/40 dark:bg-blue-950/20"
        data-testid="wellness-water-block"
      >
        <div className="flex items-center justify-between gap-2">
          <span className="pa26-caption font-semibold text-blue-800 dark:text-blue-200">
            Вода
          </span>
          <span className="pa26-card-title tabular-nums text-pa-foreground">
            {(total / 1000).toFixed(1)} л
            {pct != null ? ` · ${pct}%` : ""}
          </span>
        </div>
        {!hasExplicitTarget ? (
          <p className="pa26-micro mt-0.5 text-pa-muted">
            Цель не задана — ориентир {(DEFAULT_TARGET_ML / 1000).toFixed(1)} л
          </p>
        ) : (
          <p className="pa26-micro mt-0.5 text-pa-muted">
            Цель {(effectiveTarget / 1000).toFixed(1)} л
          </p>
        )}
        {pct != null ? (
          <V2ProgressBar percent={pct} tone="water" className="mt-2" />
        ) : null}
        <div className="mt-3 grid grid-cols-2 gap-2">
          {[250, 500].map((amount) => (
            <button
              key={amount}
              type="button"
              disabled={saving || !initData}
              onClick={() => void addWater(amount)}
              data-testid={`water-add-${amount}`}
              className="min-h-[44px] rounded-control border border-blue-300/80 bg-pa-surface px-3 py-2.5 pa26-micro font-semibold text-blue-800 transition active:scale-[0.99] disabled:opacity-50 dark:border-blue-800/50 dark:text-blue-200"
            >
              +{amount} мл
            </button>
          ))}
        </div>
        {feedback ? (
          <p className="pa26-micro mt-2 font-medium text-sage-700 dark:text-sage-300">
            {feedback}
          </p>
        ) : null}
        {error ? (
          <p className="pa26-micro mt-2 text-pa-error">{error}</p>
        ) : null}
      </section>
    );
  }

  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
            Вода
          </p>
          <p className="pa26-card-title mt-1 tabular-nums">
            {(total / 1000).toFixed(1)} л
            {pct != null ? (
              <span className="pa26-caption ml-1 font-normal text-pa-muted">
                · {pct}%
              </span>
            ) : null}
          </p>
          {hasExplicitTarget ? (
            <p className="pa26-caption mt-0.5 text-pa-muted">
              Цель {(effectiveTarget / 1000).toFixed(1)} л
            </p>
          ) : (
            <p className="pa26-caption mt-0.5 text-pa-muted">Цель не задана</p>
          )}
        </div>
        <Button2026
          size="compact"
          variant="secondary"
          disabled={saving || !initData}
          onClick={() => void addWater(GLASS_ML)}
          data-testid="water-add-250"
        >
          +250 мл
        </Button2026>
      </div>
      {pct != null ? (
        <div className="mt-3 h-2 overflow-hidden rounded-pill bg-cream-deep dark:bg-graphite-700/40">
          <div
            className={cn(
              "h-full rounded-pill bg-sage-500 transition-[width] dark:bg-sage-400",
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
      {feedback ? (
        <p className="pa26-micro mt-2 font-medium text-sage-700">{feedback}</p>
      ) : null}
      {error ? <p className="pa26-micro mt-2 text-pa-error">{error}</p> : null}
    </section>
  );
}
