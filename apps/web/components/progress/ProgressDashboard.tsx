"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ProgressProLocked } from "@/components/progress/ProgressProLocked";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { SkeletonList } from "@/components/ui/Skeleton";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createProgressEntry,
  createTrainingEntry,
  fetchProgressOverview,
  updateProgressPrivacy,
} from "@/lib/progress/api";
import {
  RETURN_TO_PARAM,
  backLabelForReturnTo,
  sanitizeReturnTo,
} from "@/lib/navigation/return-to";
import {
  STATUS_LABELS,
  formatWater,
  formatWeightDelta,
  formatWeightKg,
} from "@/lib/progress/labels";
import type { ProgressOverview } from "@/lib/progress/types";

function MacroCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="pa-card p-3">
      <p className="text-xs text-graphite-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-graphite-900">{value}</p>
    </article>
  );
}

function statusColor(status: string): string {
  if (status === "improving") return "text-sage-700 bg-sage-50";
  if (status === "attention") return "text-warm bg-warm/10";
  if (status === "hidden") return "text-graphite-500 bg-cream-deep";
  return "text-graphite-600 bg-cream-deep";
}

export function ProgressDashboard() {
  const searchParams = useSearchParams();
  const returnTo = sanitizeReturnTo(searchParams.get(RETURN_TO_PARAM), "/profile");
  const { initData, isTelegram } = useTelegram();
  const { mode } = useAppMode();
  const [data, setData] = useState<ProgressOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showWeightForm, setShowWeightForm] = useState(false);
  const [showTrainingForm, setShowTrainingForm] = useState(false);
  const [weightKg, setWeightKg] = useState("");
  const [waist, setWaist] = useState("");
  const [chest, setChest] = useState("");
  const [hips, setHips] = useState("");
  const [weightNote, setWeightNote] = useState("");
  const [trainingType, setTrainingType] = useState("Силовая");
  const [trainingMin, setTrainingMin] = useState("");
  const [trainingIntensity, setTrainingIntensity] = useState<
    "low" | "medium" | "high"
  >("medium");
  const [trainingNote, setTrainingNote] = useState("");

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const overview = await fetchProgressOverview(initData, mode);
      setData(overview);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const focus = searchParams.get("focus");
    if (focus === "weight") {
      setShowWeightForm(true);
      setShowTrainingForm(false);
    } else if (focus === "training") {
      setShowTrainingForm(true);
      setShowWeightForm(false);
    }
  }, [searchParams]);

  async function handleAddWeight(e: React.FormEvent) {
    e.preventDefault();
    if (!initData) return;
    setSaving(true);
    setError(null);
    try {
      await createProgressEntry(initData, mode, {
        weight_kg: weightKg ? parseFloat(weightKg) : null,
        waist_cm: waist ? parseFloat(waist) : null,
        chest_cm: chest ? parseFloat(chest) : null,
        hips_cm: hips ? parseFloat(hips) : null,
        notes: weightNote || null,
      });
      setShowWeightForm(false);
      setWeightKg("");
      setWaist("");
      setChest("");
      setHips("");
      setWeightNote("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddTraining(e: React.FormEvent) {
    e.preventDefault();
    if (!initData || !trainingType.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await createTrainingEntry(initData, mode, {
        training_type: trainingType.trim(),
        duration_minutes: trainingMin ? parseInt(trainingMin, 10) : null,
        intensity: trainingIntensity,
        notes: trainingNote || null,
      });
      setShowTrainingForm(false);
      setTrainingMin("");
      setTrainingNote("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function toggleFamilyVisibility() {
    if (!initData || !data) return;
    setSaving(true);
    try {
      const res = await updateProgressPrivacy(
        initData,
        mode,
        !data.show_progress_to_family,
      );
      setData({ ...data, show_progress_to_family: res.show_progress_to_family });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить");
    } finally {
      setSaving(false);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="px-4 py-16 text-center text-sm text-graphite-600">
        Откройте приложение в Telegram
      </div>
    );
  }

  if (loading || !data) {
    return (
      <ScreenLayout title="Прогресс" contentClassName="space-y-3 pb-24">
        <SkeletonList count={3} />
      </ScreenLayout>
    );
  }

  const t = data.targets;

  return (
    <ScreenLayout
      title="Прогресс"
      subtitle="ПланАм PRO — сопровождение ваших целей"
      back={{ label: backLabelForReturnTo(returnTo), href: returnTo }}
      contentClassName="space-y-3"
    >
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}

        {!data.is_pro ? (
          <ProgressProLocked goalLabel={data.goal_label} />
        ) : (
          <>
            <section className="pa-card border-sage-200 bg-sage-50/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-sage-800">
                Цель
              </p>
              <p className="mt-1 text-xl font-bold text-graphite-900">
                {data.goal_label ?? "Не задана"}
              </p>
              {data.goal_progress_percent != null ? (
                <div className="mt-3">
                  <div className="flex justify-between text-sm text-graphite-600">
                    <span>Прогресс к цели</span>
                    <span className="font-semibold text-sage-800">
                      {data.goal_progress_percent}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-pill bg-cream-deep">
                    <div
                      className="h-full rounded-pill bg-sage-500 transition-all"
                      style={{ width: `${data.goal_progress_percent}%` }}
                    />
                  </div>
                </div>
              ) : null}
            </section>

            <section className="grid grid-cols-2 gap-2">
              <MacroCard
                label="Вес сейчас"
                value={formatWeightKg(data.current_weight_kg)}
              />
              <MacroCard
                label="За неделю"
                value={formatWeightDelta(data.weight_change_week_kg)}
              />
            </section>

            {t ? (
              <section>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-graphite-500">
                  Питание в день
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <MacroCard
                    label="Калории"
                    value={t.calories_target != null ? `~${t.calories_target}` : "—"}
                  />
                  <MacroCard
                    label="Белки"
                    value={
                      t.protein_target_g != null ? `${t.protein_target_g} г` : "—"
                    }
                  />
                  <MacroCard
                    label="Жиры"
                    value={t.fat_target_g != null ? `${t.fat_target_g} г` : "—"}
                  />
                  <MacroCard
                    label="Углеводы"
                    value={
                      t.carbs_target_g != null ? `${t.carbs_target_g} г` : "—"
                    }
                  />
                  <MacroCard
                    label="Вода"
                    value={formatWater(t.water_target_ml)}
                  />
                  <MacroCard
                    label="Тренировки"
                    value={`${data.trainings_this_week} · ${data.training_minutes_week} мин`}
                  />
                </div>
              </section>
            ) : null}

            {data.pro_recommendation ? (
              <section className="pa-card border-warm/30 bg-warm/10 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-warm">
                  Совет ПланАм
                </p>
                <p className="mt-2 text-sm leading-relaxed text-graphite-800">
                  {data.pro_recommendation}
                </p>
              </section>
            ) : null}

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setShowWeightForm(true)}
                className="pa-btn-primary min-h-[44px] py-3 text-sm"
              >
                Добавить вес
              </button>
              <button
                type="button"
                onClick={() => setShowTrainingForm(true)}
                className="pa-btn min-h-[44px] border-sage-200 py-3 text-sm text-sage-800"
              >
                Добавить тренировку
              </button>
            </div>

            <section className="pa-card p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-graphite-800">
                  Показывать прогресс семье
                </p>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    checked={data.show_progress_to_family}
                    disabled={saving}
                    onChange={() => void toggleFamilyVisibility()}
                    className="peer sr-only"
                  />
                  <span className="h-6 w-10 rounded-pill bg-cream-deep transition peer-checked:bg-sage-500" />
                  <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-pill bg-cream-surface shadow-soft transition peer-checked:translate-x-4" />
                </label>
              </div>
            </section>

            {data.family_progress.length > 0 ? (
              <section className="pa-card p-4">
                <h2 className="text-sm font-bold text-graphite-900">Прогресс семьи</h2>
                <ul className="mt-3 space-y-2">
                  {data.family_progress.map((member) => (
                    <li
                      key={member.member_id}
                      className="rounded-control border border-cream-border bg-cream-deep/40 p-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="font-semibold text-graphite-900">
                            {member.name}
                            {member.is_you ? " (вы)" : ""}
                          </p>
                          {member.goal_label ? (
                            <p className="text-xs text-graphite-500">
                              {member.goal_label}
                            </p>
                          ) : null}
                        </div>
                        <span
                          className={`shrink-0 rounded-pill px-2 py-0.5 text-[10px] font-bold ${statusColor(member.status)}`}
                        >
                          {STATUS_LABELS[member.status]}
                        </span>
                      </div>
                      <p className="mt-1.5 text-sm text-graphite-600">
                        {member.progress_summary}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </>
        )}

      {showWeightForm ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4">
          <form
            onSubmit={(e) => void handleAddWeight(e)}
            className="w-full max-w-lg rounded-card bg-cream-surface p-4 shadow-lift"
          >
            <h3 className="text-lg font-bold text-graphite-900">Добавить вес</h3>
            <div className="mt-3 space-y-3">
              <label className="block text-sm">
                <span className="text-graphite-600">Вес, кг</span>
                <input
                  type="number"
                  step="0.1"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                  required
                />
              </label>
              <div className="grid grid-cols-3 gap-2">
                <label className="block text-sm">
                  <span className="text-graphite-600">Талия</span>
                  <input
                    type="number"
                    value={waist}
                    onChange={(e) => setWaist(e.target.value)}
                    className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-2 py-2 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-graphite-600">Грудь</span>
                  <input
                    type="number"
                    value={chest}
                    onChange={(e) => setChest(e.target.value)}
                    className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-2 py-2 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-graphite-600">Бёдра</span>
                  <input
                    type="number"
                    value={hips}
                    onChange={(e) => setHips(e.target.value)}
                    className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-2 py-2 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                  />
                </label>
              </div>
              <label className="block text-sm">
                <span className="text-graphite-600">Заметка</span>
                <input
                  type="text"
                  value={weightNote}
                  onChange={(e) => setWeightNote(e.target.value)}
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                />
              </label>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setShowWeightForm(false)}
                className="pa-btn flex-1 py-3 text-sm"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={saving}
                className="pa-btn-primary flex-1 py-3 text-sm disabled:opacity-50"
              >
                {saving ? "…" : "Сохранить"}
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {showTrainingForm ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4">
          <form
            onSubmit={(e) => void handleAddTraining(e)}
            className="w-full max-w-lg rounded-card bg-cream-surface p-4 shadow-lift"
          >
            <h3 className="text-lg font-bold text-graphite-900">Добавить тренировку</h3>
            <div className="mt-3 space-y-3">
              <label className="block text-sm">
                <span className="text-graphite-600">Тип</span>
                <select
                  value={trainingType}
                  onChange={(e) => setTrainingType(e.target.value)}
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                >
                  <option>Силовая</option>
                  <option>Кардио</option>
                  <option>Йога</option>
                  <option>Прогулка</option>
                  <option>Другое</option>
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-graphite-600">Длительность, мин</span>
                <input
                  type="number"
                  value={trainingMin}
                  onChange={(e) => setTrainingMin(e.target.value)}
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                />
              </label>
              <label className="block text-sm">
                <span className="text-graphite-600">Интенсивность</span>
                <select
                  value={trainingIntensity}
                  onChange={(e) =>
                    setTrainingIntensity(
                      e.target.value as "low" | "medium" | "high",
                    )
                  }
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                >
                  <option value="low">Низкая</option>
                  <option value="medium">Средняя</option>
                  <option value="high">Высокая</option>
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-graphite-600">Заметка</span>
                <input
                  type="text"
                  value={trainingNote}
                  onChange={(e) => setTrainingNote(e.target.value)}
                  className="mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                />
              </label>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setShowTrainingForm(false)}
                className="pa-btn flex-1 py-3 text-sm"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={saving}
                className="pa-btn-primary flex-1 py-3 text-sm disabled:opacity-50"
              >
                {saving ? "…" : "Сохранить"}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </ScreenLayout>
  );
}
