"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { cn } from "@/lib/planam/cn";
import { addWaterIntake, fetchWaterToday } from "@/lib/water-intake/api";

const GLASS_ML = 250;

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

  const load = useCallback(async () => {
    if (!initData) {
      return;
    }
    const data = await fetchWaterToday(initData, mode);
    setTotal(data.total_ml);
    setTarget(data.target_ml);
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addGlass() {
    if (!initData) {
      return;
    }
    setSaving(true);
    try {
      const data = await addWaterIntake(initData, mode, GLASS_ML);
      setTotal(data.total_ml);
      setTarget(data.target_ml);
      invalidateCache("progress-overview");
      onUpdated?.();
    } finally {
      setSaving(false);
    }
  }

  const pct =
    target && target > 0
      ? Math.min(100, Math.round((total / target) * 100))
      : null;

  if (compact) {
    return (
      <button
        type="button"
        disabled={saving || !initData}
        onClick={() => void addGlass()}
        className="flex w-full items-center justify-between gap-2 rounded-card border border-pa-border bg-pa-surface px-3 py-2 text-left active:scale-[0.99] dark:shadow-none"
      >
        <span className="pa26-caption text-pa-muted">Вода</span>
        <span className="pa26-card-title tabular-nums">
          {(total / 1000).toFixed(1)} л{pct != null ? ` · ${pct}%` : ""}
        </span>
      </button>
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
          {target != null ? (
            <p className="pa26-caption mt-0.5 text-pa-muted">
              Цель {(target / 1000).toFixed(1)} л
            </p>
          ) : null}
        </div>
        <Button2026
          size="compact"
          variant="secondary"
          disabled={saving || !initData}
          onClick={() => void addGlass()}
        >
          + стакан
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
    </section>
  );
}
