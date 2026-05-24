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
    <div className="rounded-xl border border-sky-100 bg-sky-50/80 p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-sky-900">
            Вода сегодня
          </p>
          <p className="mt-0.5 text-sm font-semibold text-stone-900">
            {liters} л{pct != null ? ` · ${pct}%` : ""}
          </p>
          {target != null ? (
            <p className="text-xs text-stone-500">Цель: {targetLiters}</p>
          ) : null}
        </div>
        <button
          type="button"
          disabled={saving}
          onClick={() => void addGlass()}
          className="shrink-0 rounded-xl bg-sky-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
        >
          +{GLASS_ML} мл
        </button>
      </div>
      {pct != null ? (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-sky-100">
          <div
            className="h-full rounded-full bg-sky-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}
