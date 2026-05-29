"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { addWaterIntake, fetchWaterToday } from "@/lib/water-intake/api";

const GLASS_ML = 250;

type Props = {
  onUpdated?: () => void;
};

export function WaterIntakePanel({ onUpdated }: Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [total, setTotal] = useState(0);
  const [target, setTarget] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!initData) return;
    const data = await fetchWaterToday(initData, mode);
    setTotal(data.total_ml);
    setTarget(data.target_ml);
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addGlass() {
    if (!initData) return;
    setSaving(true);
    try {
      const data = await addWaterIntake(initData, mode, GLASS_ML);
      setTotal(data.total_ml);
      setTarget(data.target_ml);
      onUpdated?.();
    } finally {
      setSaving(false);
    }
  }

  const liters = (total / 1000).toFixed(1);
  const targetLiters =
    target != null ? `${(target / 1000).toFixed(1)} л` : "—";
  const pct =
    target && target > 0 ? Math.min(100, Math.round((total / target) * 100)) : null;

  return (
    <div className="rounded-control border border-sage-200 bg-sage-50/50 p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-sage-800">
            Вода сегодня
          </p>
          <p className="mt-0.5 text-sm font-semibold text-graphite-900">
            {liters} л{pct != null ? ` · ${pct}%` : ""}
          </p>
          {target != null ? (
            <p className="text-xs text-graphite-500">Цель: {targetLiters}</p>
          ) : null}
        </div>
        <button
          type="button"
          disabled={saving}
          onClick={() => void addGlass()}
          className="pa-btn-primary shrink-0 px-3 py-2 text-xs disabled:opacity-50"
        >
          +{GLASS_ML} мл
        </button>
      </div>
      {pct != null ? (
        <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-sage-100">
          <div
            className="h-full rounded-pill bg-sage-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}
