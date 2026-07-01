"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { OptionCards } from "@/components/onboarding/OptionCards";
import { TextAreaField } from "@/components/onboarding/TextAreaField";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { NutritionGoalDetailsFields } from "@/components/nutrition-profile/NutritionGoalDetailsFields";
import { NutritionSection } from "@/components/nutrition-profile/NutritionSection";
import { NumberInput } from "@/components/nutrition-profile/NumberInput";
import { ToggleRow } from "@/components/nutrition-profile/ToggleRow";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { fetchMyFamily, setAllowAdminProfileEdit } from "@/lib/family/api";
import {
  RETURN_TO_PARAM,
  backLabelForReturnTo,
  readReturnTo,
} from "@/lib/navigation/return-to";
import { usePlanam2026Embedded } from "@/lib/planam/embedded-2026";
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
  getNutritionSectionChecks,
  isNutritionCardComplete,
  NUTRITION_SECTION_LABELS,
  type NutritionSectionId,
} from "@/lib/nutrition-profile/sections";
import {
  INITIAL_NUTRITION_PROFILE,
  type NutritionProfileData,
} from "@/lib/nutrition-profile/types";

function basicsSummary(data: NutritionProfileData): string {
  const parts: string[] = [];
  if (data.age) parts.push(`${data.age} лет`);
  const g = GENDER_OPTIONS.find((o) => o.value === data.gender)?.label;
  if (g) parts.push(g);
  if (data.height_cm && data.weight_kg) {
    parts.push(`${data.height_cm} см, ${data.weight_kg} кг`);
  }
  return parts.length ? parts.join(" · ") : "Не заполнено";
}

function goalActivitySummary(data: NutritionProfileData): string {
  const goal = data.nutrition_goal
    ? (NUTRITION_GOAL_LABELS[data.nutrition_goal] ?? data.nutrition_goal)
    : null;
  const act = ACTIVITY_OPTIONS.find((o) => o.value === data.activity_level)?.label;
  return [goal, act].filter(Boolean).join(" · ") || "Не заполнено";
}

function allergiesSummary(data: NutritionProfileData): string {
  const n =
    data.allergies.filter((a) => a !== "none").length +
    data.diets.filter((d) => d !== "none").length;
  const extra = [data.medical_restrictions, data.banned_foods].filter(Boolean)
    .length;
  if (!n && !extra) return "Без ограничений";
  return `${n + extra} настроек`;
}

function proSummary(data: NutritionProfileData): string {
  if (!data.pro.workouts_enabled && !data.pro.track_macros) return "Выключено";
  const parts: string[] = [];
  if (data.pro.workouts_enabled) parts.push("тренировки");
  if (data.pro.track_macros) parts.push("КБЖУ");
  return parts.join(", ");
}

export function NutritionProfileForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const embedded = usePlanam2026Embedded("/account/nutrition");
  const returnTo = readReturnTo(
    searchParams,
    "/account",
  );
  const { showToast } = useToast();
  const { initData } = useTelegram();
  const [data, setData] = useState<NutritionProfileData>(INITIAL_NUTRITION_PROFILE);
  const [savedData, setSavedData] = useState<NutritionProfileData>(
    INITIAL_NUTRITION_PROFILE,
  );
  const [openSection, setOpenSection] = useState<NutritionSectionId | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allowAdminEdit, setAllowAdminEdit] = useState(false);
  const [inFamily, setInFamily] = useState(false);

  const progress = useMemo(() => getNutritionSectionChecks(data), [data]);
  const isDirty = useMemo(
    () => JSON.stringify(data) !== JSON.stringify(savedData),
    [data, savedData],
  );

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [profile, family] = await Promise.all([
        fetchNutritionProfile(initData),
        fetchMyFamily(initData).catch(() => null),
      ]);
      setData(profile);
      setSavedData(profile);
      const you = family?.members.find((m) => m.is_you && !m.is_virtual);
      setInFamily(Boolean(you));
      setAllowAdminEdit(you?.allow_admin_profile_edit ?? false);
    } catch {
      setError("Не удалось загрузить профиль");
    } finally {
      setLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = useCallback((partial: Partial<NutritionProfileData>) => {
    setData((prev) => ({ ...prev, ...partial }));
  }, []);

  const patchPro = useCallback(
    (partial: Partial<NutritionProfileData["pro"]>) => {
      setData((prev) => ({ ...prev, pro: { ...prev.pro, ...partial } }));
    },
    [],
  );

  const summaries = useMemo(
    () => ({
      basics: basicsSummary(data),
      goal_activity: goalActivitySummary(data),
      allergies_restrictions: allergiesSummary(data),
      favorites: data.favorite_foods.trim() ? "Указано" : "Не заполнено",
      dislikes: data.disliked_foods.trim() ? "Указано" : "Не заполнено",
      cooking:
        BUDGET_OPTIONS.find((o) => o.value === data.budget)?.label &&
        COOKING_TIME_OPTIONS.find((o) => o.value === data.cooking_time)?.label
          ? "Настроено"
          : "Не заполнено",
      pro: proSummary(data),
    }),
    [data],
  );

  async function handleSave() {
    if (!initData) return;
    if (!data.nutrition_goal) {
      setError("Выберите цель питания");
      setOpenSection("goal_activity");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await saveNutritionProfile(initData, { ...data, completed: true });
      setSavedData(data);
      // Profile drives KBJU / advice / home cards — invalidate.
      invalidateCache("nutrition-profile");
      invalidateCache("progress-overview");
      await showToast("✓ Сохранено");
      router.replace(returnTo);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  function toggleSection(id: NutritionSectionId) {
    setOpenSection((prev) => (prev === id ? null : id));
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center px-5">
        <p className="text-sm text-graphite-500">Загрузка профиля…</p>
      </div>
    );
  }

  const saveBar = isDirty ? (
    <StickyBottomBar>
      <button
        type="button"
        disabled={saving || !initData}
        onClick={() => void handleSave()}
        className="pa-btn-primary w-full py-3.5 text-base disabled:opacity-50"
      >
        {saving ? "Сохранение…" : "Сохранить"}
      </button>
    </StickyBottomBar>
  ) : null;

  const content = (
    <>
      <section className="rounded-card border border-sage-200 bg-sage-50/50 p-4 shadow-soft dark:border-sage-700/40 dark:bg-sage-900/20 dark:shadow-none">
        <div className="mb-2 flex items-center justify-between text-sm text-pa-foreground">
          <span className="font-medium">
            Заполнено {progress.filled} из {progress.total} разделов
          </span>
          <span className="font-bold text-sage-800 dark:text-sage-200">{progress.percent}%</span>
        </div>
        <div
          className="h-2 overflow-hidden rounded-pill bg-sage-100 dark:bg-sage-900/40"
          role="progressbar"
          aria-valuenow={progress.percent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-pill bg-sage-600 transition-all"
            style={{ width: `${progress.percent}%` }}
          />
        </div>
      </section>

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">
          Что PLANAM учитывает в меню
        </h2>
        <p className="mt-1 text-xs leading-relaxed text-pa-muted">
          Ограничения, аллергии, любимые и нелюбимые продукты используются при
          подборе рецептов и списке покупок. Достаточно выбрать цель и ограничения —
          детали можно заполнить позже.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "Аллергии",
            "Не ем",
            "Люблю",
            "Не люблю",
            "Медицинские ограничения",
            "Религия и этика",
            "Спорт-цели",
          ].map((label) => (
            <span
              key={label}
              className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-pa-muted dark:bg-pa-elevated"
            >
              {label}
            </span>
          ))}
        </div>
      </section>

      {error ? (
        <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <div className="mt-3 space-y-3">
        <NutritionSection
          id="basics"
          title={NUTRITION_SECTION_LABELS.basics}
          summary={summaries.basics}
          complete={isNutritionCardComplete("basics", data)}
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
                <p className="mb-1.5 text-sm font-medium text-pa-foreground">Пол</p>
                <div className="flex flex-wrap gap-2">
                  {GENDER_OPTIONS.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      onClick={() => patch({ gender: o.value })}
                      className={`pa-chip ${
                        data.gender === o.value
                          ? "border-sage-500 bg-sage-50 text-sage-900"
                          : "border-pa-border bg-pa-surface text-pa-muted"
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
          id="goal_activity"
          title={NUTRITION_SECTION_LABELS.goal_activity}
          summary={summaries.goal_activity}
          complete={isNutritionCardComplete("goal_activity", data)}
          open={openSection === "goal_activity"}
          onToggle={() => toggleSection("goal_activity")}
        >
          <div className="space-y-5">
            <div>
              <p className="mb-1 text-sm font-medium text-pa-foreground">Цель</p>
              <p className="mb-2 text-xs leading-relaxed text-pa-muted">
                Выберите основной сценарий: поддержание, похудение, набор массы,
                здоровое питание или спортивный режим.
              </p>
              <OptionCards
                options={NUTRITION_GOAL_OPTIONS}
                value={data.nutrition_goal}
                onChange={(nutrition_goal) => patch({ nutrition_goal })}
                compact
              />
              <NutritionGoalDetailsFields
                goal={data.nutrition_goal}
                details={data.goal_details}
                profile={data}
                onChange={(goal_details) => patch({ goal_details })}
                onProfilePatch={patch}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">Активность</p>
              <OptionCards
                options={ACTIVITY_OPTIONS}
                value={data.activity_level}
                onChange={(activity_level) => patch({ activity_level })}
                compact
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="allergies_restrictions"
          title={NUTRITION_SECTION_LABELS.allergies_restrictions}
          summary={summaries.allergies_restrictions}
          complete={isNutritionCardComplete("allergies_restrictions", data)}
          open={openSection === "allergies_restrictions"}
          onToggle={() => toggleSection("allergies_restrictions")}
        >
          <div className="space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">Аллергии</p>
              <ChipSelect
                options={ALLERGY_OPTIONS}
                value={data.allergies}
                onChange={(allergies) => patch({ allergies })}
                exclusiveNone="none"
                compact
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">Диеты и ограничения</p>
              <ChipSelect
                options={DIET_OPTIONS}
                value={data.diets}
                onChange={(diets) => patch({ diets })}
                exclusiveNone="none"
                compact
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">
                Медицинские ограничения
              </p>
              <TextAreaField
                value={data.medical_restrictions}
                onChange={(medical_restrictions) =>
                  patch({ medical_restrictions })
                }
                placeholder="Например: диабет, гастрит…"
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">
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
          id="favorites"
          title={NUTRITION_SECTION_LABELS.favorites}
          summary={summaries.favorites}
          complete={isNutritionCardComplete("favorites", data)}
          open={openSection === "favorites"}
          onToggle={() => toggleSection("favorites")}
        >
          <TextAreaField
            value={data.favorite_foods}
            onChange={(favorite_foods) => patch({ favorite_foods })}
            placeholder="Например: каши, ягоды, супы"
          />
        </NutritionSection>

        <NutritionSection
          id="dislikes"
          title={NUTRITION_SECTION_LABELS.dislikes}
          summary={summaries.dislikes}
          complete={isNutritionCardComplete("dislikes", data)}
          open={openSection === "dislikes"}
          onToggle={() => toggleSection("dislikes")}
        >
          <TextAreaField
            value={data.disliked_foods}
            onChange={(disliked_foods) => patch({ disliked_foods })}
            placeholder="Например: рыбу, острое, брокколи"
          />
        </NutritionSection>

        <NutritionSection
          id="cooking"
          title={NUTRITION_SECTION_LABELS.cooking}
          summary={summaries.cooking}
          complete={isNutritionCardComplete("cooking", data)}
          open={openSection === "cooking"}
          onToggle={() => toggleSection("cooking")}
        >
          <div className="space-y-5">
            <div>
              <p className="mb-1 text-sm font-medium text-pa-foreground">Бюджет</p>
              <p className="mb-2 text-xs leading-relaxed text-pa-muted">
                Эконом — простые продукты, средний — баланс, премиум — больше
                рыбы, ягод, орехов и специальных продуктов.
              </p>
              <OptionCards
                options={BUDGET_OPTIONS}
                value={data.budget}
                onChange={(budget) => patch({ budget })}
                compact
              />
            </div>
            <div>
              <p className="mb-1 text-sm font-medium text-pa-foreground">Время готовки</p>
              <p className="mb-2 text-xs leading-relaxed text-pa-muted">
                Помогает выбирать быстрые блюда в будни и более спокойные
                рецепты на свободные дни.
              </p>
              <ChipSelect
                options={COOKING_TIME_OPTIONS}
                value={data.cooking_time ? [data.cooking_time] : []}
                onChange={(values) => patch({ cooking_time: values[0] ?? null })}
                multiple={false}
                compact
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-pa-foreground">Сложность блюд</p>
              <OptionCards
                options={DISH_COMPLEXITY_OPTIONS}
                value={data.dish_complexity}
                onChange={(dish_complexity) => patch({ dish_complexity })}
                compact
              />
            </div>
          </div>
        </NutritionSection>

        <NutritionSection
          id="pro"
          title={NUTRITION_SECTION_LABELS.pro}
          summary={summaries.pro}
          complete={isNutritionCardComplete("pro", data)}
          open={openSection === "pro"}
          onToggle={() => toggleSection("pro")}
        >
          <div className="space-y-4">
            <p className="text-xs text-pa-muted">
              Расширенные настройки для спорта и контроля.
            </p>
            <ToggleRow
              label="Учитывать тренировки"
              checked={data.pro.workouts_enabled}
              onChange={(workouts_enabled) => patchPro({ workouts_enabled })}
            />
            {data.pro.workouts_enabled ? (
              <>
                <TextAreaField
                  value={data.pro.workout_goal}
                  onChange={(workout_goal) => patchPro({ workout_goal })}
                  placeholder="Сила, выносливость, похудение…"
                />
                <OptionCards
                  options={WORKOUT_FREQUENCY_OPTIONS}
                  value={data.pro.workout_frequency}
                  onChange={(workout_frequency) =>
                    patchPro({ workout_frequency })
                  }
                  compact
                />
              </>
            ) : null}
            <TextAreaField
              value={data.pro.body_measurements}
              onChange={(body_measurements) =>
                patchPro({ body_measurements })
              }
              placeholder="Талия, бёдра — по желанию"
            />
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

        {inFamily ? (
          <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
            <ToggleRow
              label="Разрешить админу семьи помогать с профилем"
              description="Админ сможет менять цели и ограничения за вас"
              checked={allowAdminEdit}
              onChange={(checked) => {
                setAllowAdminEdit(checked);
                if (initData) {
                  void setAllowAdminProfileEdit(initData, checked).catch(() => {
                    setAllowAdminEdit(!checked);
                  });
                }
              }}
            />
          </section>
        ) : null}
      </div>
    </>
  );

  if (embedded) {
    return (
      <div
        className={`mx-auto max-w-lg px-4 pt-[max(0.75rem,env(safe-area-inset-top))] ${
          isDirty ? "pb-32" : "pb-6"
        }`}
      >
        <h1 className="pa26-page-title mb-4">Питание</h1>
        {content}
        {saveBar}
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Профиль питания"
      subtitle="Откройте раздел и сохраните изменения"
      back={{ label: backLabelForReturnTo(returnTo), href: returnTo }}
      footer={saveBar}
    >
      {content}
    </ScreenLayout>
  );
}
