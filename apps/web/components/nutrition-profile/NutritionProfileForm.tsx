"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { OptionCards } from "@/components/onboarding/OptionCards";
import { TextAreaField } from "@/components/onboarding/TextAreaField";
import { NutritionSection } from "@/components/nutrition-profile/NutritionSection";
import { NumberInput } from "@/components/nutrition-profile/NumberInput";
import { ToggleRow } from "@/components/nutrition-profile/ToggleRow";
import Link from "next/link";

import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchNutritionProfile,
  saveNutritionProfile,
} from "@/lib/nutrition-profile/api";
import {
  ACTIVITY_OPTIONS,
  ALLERGY_OPTIONS,
  BUDGET_OPTIONS,
  COOKING_TIME_OPTIONS,
  DIET_OPTIONS,
  DISH_COMPLEXITY_OPTIONS,
  GENDER_OPTIONS,
  NUTRITION_GOAL_LABELS,
  NUTRITION_GOAL_OPTIONS,
  WORKOUT_FREQUENCY_OPTIONS,
} from "@/lib/nutrition-profile/options";
import {
  INITIAL_NUTRITION_PROFILE,
  type NutritionProfileData,
} from "@/lib/nutrition-profile/types";

type SectionId =
  | "basics"
  | "goal"
  | "activity"
  | "limits"
  | "tastes"
  | "cooking"
  | "pro";

function basicsSummary(data: NutritionProfileData): string {
  const parts: string[] = [];
  if (data.age) parts.push(`${data.age} лет`);
  if (data.gender) {
    const g = GENDER_OPTIONS.find((o) => o.value === data.gender)?.label;
    if (g) parts.push(g);
  }
  if (data.height_cm && data.weight_kg) {
    parts.push(`${data.height_cm} см, ${data.weight_kg} кг`);
  }
  return parts.length ? parts.join(" · ") : "Не заполнено";
}

function goalSummary(data: NutritionProfileData): string {
  if (!data.nutrition_goal) return "Выберите цель";
  return NUTRITION_GOAL_LABELS[data.nutrition_goal] ?? data.nutrition_goal;
}

function activitySummary(data: NutritionProfileData): string {
  const o = ACTIVITY_OPTIONS.find((x) => x.value === data.activity_level);
  return o?.label ?? "Не выбрана";
}

function limitsSummary(data: NutritionProfileData): string {
  const n =
    data.allergies.filter((a) => a !== "none").length + data.diets.filter((d) => d !== "none").length;
  const extra = [data.medical_restrictions, data.banned_foods].filter(Boolean).length;
  if (!n && !extra) return "Без ограничений";
  return `${n + extra} настроек`;
}

function tastesSummary(data: NutritionProfileData): string {
  if (data.favorite_foods.trim()) return "Любимое указано";
  if (data.disliked_foods.trim()) return "Нелюбимое указано";
  return "Не заполнено";
}

function cookingSummary(data: NutritionProfileData): string {
  const b = BUDGET_OPTIONS.find((o) => o.value === data.budget)?.label;
  const t = COOKING_TIME_OPTIONS.find((o) => o.value === data.cooking_time)?.label;
  const parts = [b, t].filter(Boolean);
  return parts.length ? parts.join(" · ") : "Не заполнено";
}

function proSummary(data: NutritionProfileData): string {
  if (!data.pro.workouts_enabled && !data.pro.track_macros) {
    return "Выключено";
  }
  const parts: string[] = [];
  if (data.pro.workouts_enabled) parts.push("тренировки");
  if (data.pro.track_macros) parts.push("КБЖУ");
  return parts.join(", ");
}

export function NutritionProfileForm() {
  const { initData } = useTelegram();
  const [data, setData] = useState<NutritionProfileData>(INITIAL_NUTRITION_PROFILE);
  const [openSection, setOpenSection] = useState<SectionId | null>("goal");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const profile = await fetchNutritionProfile(initData);
      setData(profile);
    } catch {
      setError("Не удалось загрузить профиль");
    } finally {
      setLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = useCallback(
    (partial: Partial<NutritionProfileData>) => {
      setData((prev) => ({ ...prev, ...partial }));
      setSavedAt(null);
    },
    [],
  );

  const patchPro = useCallback(
    (partial: Partial<NutritionProfileData["pro"]>) => {
      setData((prev) => ({ ...prev, pro: { ...prev.pro, ...partial } }));
      setSavedAt(null);
    },
    [],
  );

  const summaries = useMemo(
    () => ({
      basics: basicsSummary(data),
      goal: goalSummary(data),
      activity: activitySummary(data),
      limits: limitsSummary(data),
      tastes: tastesSummary(data),
      cooking: cookingSummary(data),
      pro: proSummary(data),
    }),
    [data],
  );

  async function handleSave() {
    if (!initData) return;
    if (!data.nutrition_goal) {
      setError("Выберите цель питания");
      setOpenSection("goal");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const saved = await saveNutritionProfile(initData, {
        ...data,
        completed: true,
      });
      setData(saved);
      setSavedAt(new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  function toggleSection(id: SectionId) {
    setOpenSection((prev) => (prev === id ? null : id));
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center px-5">
        <p className="text-sm text-stone-500">Загрузка профиля…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 pb-28">
      <header className="border-b border-stone-100 bg-white px-4 pb-3 pt-7 sm:px-5">
        <div className="mx-auto max-w-lg">
          <Link
            href="/profile"
            className="mb-2 inline-block text-sm font-semibold text-emerald-700"
          >
            ← Профиль
          </Link>
          <h1 className="text-2xl font-bold text-stone-900">Мой профиль питания</h1>
          <p className="mt-1 text-sm text-stone-500">
            Откройте нужный раздел и сохраните изменения
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-lg space-y-3 px-4 py-4 sm:px-5">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}
        {savedAt ? (
          <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            Сохранено в {savedAt}
          </p>
        ) : null}

        <NutritionSection
          id="basics"
          title="Основное"
          summary={summaries.basics}
          open={openSection === "basics"}
          onToggle={() => toggleSection("basics")}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <NumberInput
                label="Возраст"
                value={data.age}
                onChange={(age) => patch({ age })}
                min={1}
                max={120}
                placeholder="30"
              />
              <div>
                <p className="mb-1.5 text-sm font-medium text-stone-700">Пол</p>
                <div className="flex flex-wrap gap-2">
                  {GENDER_OPTIONS.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      onClick={() => patch({ gender: o.value })}
                      className={`rounded-full border px-3 py-2 text-sm font-medium ${
                        data.gender === o.value
                          ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                          : "border-stone-200 bg-white text-stone-700"
                      }`}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <NumberInput
                label="Рост"
                value={data.height_cm}
                onChange={(height_cm) => patch({ height_cm })}
                min={50}
                max={250}
                unit="см"
                placeholder="170"
              />
              <NumberInput
                label="Вес"
                value={data.weight_kg}
                onChange={(weight_kg) => patch({ weight_kg })}
                min={20}
                max={300}
                step={0.1}
                unit="кг"
                placeholder="70"
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="goal"
          title="Цель"
          summary={summaries.goal}
          open={openSection === "goal"}
          onToggle={() => toggleSection("goal")}
        >
          <OptionCards
            options={NUTRITION_GOAL_OPTIONS}
            value={data.nutrition_goal}
            onChange={(nutrition_goal) => patch({ nutrition_goal })}
          />
        </NutritionSection>

        <NutritionSection
          id="activity"
          title="Активность"
          summary={summaries.activity}
          open={openSection === "activity"}
          onToggle={() => toggleSection("activity")}
        >
          <OptionCards
            options={ACTIVITY_OPTIONS}
            value={data.activity_level}
            onChange={(activity_level) => patch({ activity_level })}
          />
        </NutritionSection>

        <NutritionSection
          id="limits"
          title="Ограничения"
          summary={summaries.limits}
          open={openSection === "limits"}
          onToggle={() => toggleSection("limits")}
        >
          <div className="space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Аллергии</p>
              <ChipSelect
                options={ALLERGY_OPTIONS}
                value={data.allergies}
                onChange={(allergies) => patch({ allergies })}
                exclusiveNone="none"
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Диеты</p>
              <ChipSelect
                options={DIET_OPTIONS}
                value={data.diets}
                onChange={(diets) => patch({ diets })}
                exclusiveNone="none"
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">
                Медицинские ограничения
              </p>
              <TextAreaField
                value={data.medical_restrictions}
                onChange={(medical_restrictions) => patch({ medical_restrictions })}
                placeholder="Например: диабет, гастрит, беременность…"
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">
                Запрещённые продукты
              </p>
              <TextAreaField
                value={data.banned_foods}
                onChange={(banned_foods) => patch({ banned_foods })}
                placeholder="Что нельзя ни при каких условиях"
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="tastes"
          title="Вкусы"
          summary={summaries.tastes}
          open={openSection === "tastes"}
          onToggle={() => toggleSection("tastes")}
        >
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Люблю</p>
              <TextAreaField
                value={data.favorite_foods}
                onChange={(favorite_foods) => patch({ favorite_foods })}
                placeholder="Продукты и блюда, которые хотите чаще"
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Не люблю</p>
              <TextAreaField
                value={data.disliked_foods}
                onChange={(disliked_foods) => patch({ disliked_foods })}
                placeholder="Чего лучше избегать в меню"
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="cooking"
          title="Готовка"
          summary={summaries.cooking}
          open={openSection === "cooking"}
          onToggle={() => toggleSection("cooking")}
        >
          <div className="space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Бюджет</p>
              <OptionCards
                options={BUDGET_OPTIONS}
                value={data.budget}
                onChange={(budget) => patch({ budget })}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Время готовки</p>
              <ChipSelect
                options={COOKING_TIME_OPTIONS}
                value={data.cooking_time ? [data.cooking_time] : []}
                onChange={(values) =>
                  patch({ cooking_time: values[0] ?? null })
                }
                multiple={false}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Сложность блюд</p>
              <OptionCards
                options={DISH_COMPLEXITY_OPTIONS}
                value={data.dish_complexity}
                onChange={(dish_complexity) => patch({ dish_complexity })}
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="pro"
          title="PRO"
          summary={summaries.pro}
          open={openSection === "pro"}
          onToggle={() => toggleSection("pro")}
        >
          <div className="space-y-4">
            <p className="text-xs text-stone-500">
              Расширенные настройки для спорта и контроля. Можно заполнить позже.
            </p>
            <ToggleRow
              label="Учитывать тренировки"
              checked={data.pro.workouts_enabled}
              onChange={(workouts_enabled) => patchPro({ workouts_enabled })}
            />
            {data.pro.workouts_enabled ? (
              <>
                <div>
                  <p className="mb-2 text-sm font-medium text-stone-700">
                    Цель тренировок
                  </p>
                  <TextAreaField
                    value={data.pro.workout_goal}
                    onChange={(workout_goal) => patchPro({ workout_goal })}
                    placeholder="Сила, выносливость, похудение…"
                  />
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium text-stone-700">Частота</p>
                  <OptionCards
                    options={WORKOUT_FREQUENCY_OPTIONS}
                    value={data.pro.workout_frequency}
                    onChange={(workout_frequency) =>
                      patchPro({ workout_frequency })
                    }
                  />
                </div>
              </>
            ) : null}
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Замеры тела</p>
              <TextAreaField
                value={data.pro.body_measurements}
                onChange={(body_measurements) =>
                  patchPro({ body_measurements })
                }
                placeholder="Талия, бёдра, % жира — по желанию"
              />
            </div>
            <NumberInput
              label="Вода в день"
              value={data.pro.water_liters}
              onChange={(water_liters) => patchPro({ water_liters })}
              min={0}
              max={10}
              step={0.1}
              unit="л"
              placeholder="2"
            />
            <ToggleRow
              label="Следить за КБЖУ"
              description="Учитывать в меню и рекомендациях"
              checked={data.pro.track_macros}
              onChange={(track_macros) => patchPro({ track_macros })}
            />
          </div>
        </NutritionSection>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-stone-200/90 bg-white/95 px-4 py-3 backdrop-blur-md pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        <div className="mx-auto max-w-lg">
          <button
            type="button"
            disabled={saving || !initData}
            onClick={() => void handleSave()}
            className="w-full rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/50 transition hover:bg-emerald-700 disabled:opacity-50 active:scale-[0.99]"
          >
            {saving ? "Сохранение…" : "Сохранить профиль"}
          </button>
        </div>
      </div>

    </div>
  );
}
