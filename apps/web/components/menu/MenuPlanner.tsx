"use client";

import Link from "next/link";

import { ApiRequestError } from "@/lib/api-errors";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuChooseVariants } from "@/components/menu/MenuChooseVariants";
import { MenuPlannerSection } from "@/components/menu/MenuPlannerSection";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  buildChecklistState,
  buildRestrictionsSummary,
  formatGoalLabel,
} from "@/lib/menu/planner-summary";
import {
  CHECKLIST_ITEMS,
  PLAN_MODE_OPTIONS,
  type PlanModeId,
} from "@/lib/menu/planner-options";
import {
  loadPersonsOverride,
  loadPlanMode,
  savePlanMode,
} from "@/lib/menu/planner-storage";
import {
  fetchSelectedMenu,
  generateMenus,
  selectMenu,
} from "@/lib/menu/api";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchPantry } from "@/lib/pantry/api";
import type { SelectedMenu } from "@/lib/menu/types";
import type { MenuVariant } from "@/lib/menu/types";

type Phase = "setup" | "choose";

export function MenuPlanner() {
  const { initData, isTelegram } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [phase, setPhase] = useState<Phase>("setup");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(null);
  const [generatedMenus, setGeneratedMenus] = useState<MenuVariant[]>([]);
  const [previewMenu, setPreviewMenu] = useState<MenuVariant | null>(null);

  const [personsCount, setPersonsCount] = useState(1);
  const [planMode, setPlanMode] = useState<PlanModeId>("healthy");
  const [displayGoal, setDisplayGoal] = useState<string | null>(null);
  const [checklistPantry, setChecklistPantry] = useState<
    Awaited<ReturnType<typeof fetchPantry>> | null
  >(null);

  const defaultPersons = useMemo(() => {
    if (mode === "family" && context?.family) {
      return context.family.members_count ?? context.family.members.length;
    }
    return 1;
  }, [mode, context]);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [nutrition, selected, pantry] = await Promise.all([
        fetchNutritionProfile(initData).catch(() => null),
        fetchSelectedMenu(initData, mode),
        fetchPantry(initData, mode).catch(() => null),
      ]);
      setProfile(nutrition);
      setSelectedMenu(selected);
      setDisplayGoal(nutrition?.nutrition_goal ?? null);

      const storedPersons = loadPersonsOverride();
      setPersonsCount(storedPersons ?? defaultPersons);

      const storedMode = loadPlanMode() as PlanModeId | null;
      if (storedMode && PLAN_MODE_OPTIONS.some((o) => o.value === storedMode)) {
        setPlanMode(storedMode);
      }

      setChecklistPantry(pantry);
    } catch {
      setError("Не удалось загрузить данные");
    } finally {
      setLoading(false);
    }
  }, [initData, mode, defaultPersons]);

  useEffect(() => {
    if (modeLoading) {
      setLoading(true);
      return;
    }
    void load();
  }, [load, modeLoading]);

  useEffect(() => {
    setPersonsCount((prev) => {
      const stored = loadPersonsOverride();
      if (stored !== null) return stored;
      return defaultPersons;
    });
  }, [defaultPersons]);

  const restrictions = buildRestrictionsSummary(profile);
  const checklist = buildChecklistState(profile, personsCount, checklistPantry);
  const hasPlan = Boolean(selectedMenu?.menu);

  function changePlanMode(id: PlanModeId) {
    setPlanMode(id);
    savePlanMode(id);
  }

  async function handleGenerate() {
    if (!initData) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await generateMenus(initData, mode, {
        persons_count: personsCount,
        plan_mode: planMode,
      });
      setGeneratedMenus(result.menus);
      setPhase("choose");
    } catch (err) {
      if (err instanceof ApiRequestError) {
        let text = err.message;
        if (err.code === "menu_generation_limit" && err.canPayWithAms) {
          text = `${text} Дополнительная генерация спишет Амы с баланса.`;
        }
        if (err.code === "menu_generation_limit" || err.code === "trial_expired") {
          text = `${text} `;
        }
        setError(text.trim());
      } else {
        setError(
          err instanceof Error ? err.message : "Не удалось составить план",
        );
      }
    } finally {
      setGenerating(false);
    }
  }

  async function handleSelect(menu: MenuVariant) {
    if (!initData) return;
    setSelecting(true);
    setError(null);
    try {
      const saved = await selectMenu(initData, mode, menu);
      setSelectedMenu(saved);
      setGeneratedMenus([]);
      setPhase("setup");
      setPreviewMenu(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить план");
    } finally {
      setSelecting(false);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-stone-600">
          План питания доступен в Telegram Mini App.
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-emerald-700">
          На главную
        </Link>
      </div>
    );
  }

  if (loading || modeLoading) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка…" />
      </div>
    );
  }

  const selectedDate = selectedMenu?.selected_at
    ? new Date(selectedMenu.selected_at).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "short",
      })
    : null;

  return (
    <div className="min-h-screen bg-stone-50 pb-28">
      <header className="border-b border-stone-100 bg-white px-4 py-4">
        <div className="mx-auto max-w-lg">
          <Link href="/menu" className="text-sm font-semibold text-emerald-700">
            ← Меню
          </Link>
          {phase === "choose" ? (
            <button
              type="button"
              onClick={() => {
                setPhase("setup");
                setGeneratedMenus([]);
              }}
              className="mt-2 block text-sm font-semibold text-emerald-700"
            >
              ← Назад к настройкам
            </button>
          ) : null}
          <h1 className="mt-1 text-xl font-bold text-stone-900">Составить меню</h1>
          <p className="mt-0.5 text-sm text-stone-500">
            {personsCount === 1
              ? "На 1 человека"
              : `На ${personsCount} человек`}
            {" · "}
            вы выбираете финальный план
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        {error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <p>{error}</p>
            {error.includes("Лимит") || error.includes("Пробный") ? (
              <Link
                href="/subscription"
                className="mt-2 inline-block font-semibold text-emerald-800"
              >
                Тариф и Амы →
              </Link>
            ) : null}
          </div>
        ) : null}

        {phase === "choose" ? (
          <MenuChooseVariants
            menus={generatedMenus}
            selecting={selecting}
            onSelect={(menu) => void handleSelect(menu)}
            onPreview={setPreviewMenu}
          />
        ) : (
          <>
            <MenuPlannerSection title="Для кого">
              {mode === "family" && context?.family ? (
                <>
                  <p className="text-sm font-medium text-stone-800">
                    {context.family.name}
                  </p>
                  <p className="mt-0.5 text-sm text-stone-500">
                    {personsCount}{" "}
                    {personsCount === 1 ? "участник" : personsCount < 5 ? "участника" : "участников"}
                  </p>
                </>
              ) : (
                <p className="text-sm font-medium text-stone-800">1 человек</p>
              )}
              <Link
                href="/menu/settings"
                className="mt-2 inline-block text-xs font-semibold text-emerald-700"
              >
                Изменить число порций →
              </Link>
            </MenuPlannerSection>

            <MenuPlannerSection
              title="Цель"
              action={
                <Link
                  href="/profile/nutrition"
                  className="text-xs font-semibold text-emerald-700"
                >
                  Изменить
                </Link>
              }
            >
              <p className="text-base font-semibold text-stone-900">
                {formatGoalLabel(displayGoal)}
              </p>
            </MenuPlannerSection>

            <MenuPlannerSection title="Режим плана">
              <div className="flex flex-wrap gap-2">
                {PLAN_MODE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => changePlanMode(option.value)}
                    className={`rounded-full border px-3 py-2 text-left text-sm transition ${
                      planMode === option.value
                        ? "border-emerald-600 bg-emerald-50 font-semibold text-emerald-900"
                        : "border-stone-200 bg-white text-stone-700"
                    }`}
                  >
                    <span className="block">{option.label}</span>
                  </button>
                ))}
              </div>
            </MenuPlannerSection>

            <MenuPlannerSection title="Ограничения">
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between gap-2">
                  <dt className="text-stone-500">Аллергии</dt>
                  <dd className="text-right font-medium text-stone-800">
                    {restrictions.allergies}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-stone-500">Диеты</dt>
                  <dd className="text-right font-medium text-stone-800">
                    {restrictions.diets}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-stone-500">Не любит</dt>
                  <dd className="max-w-[55%] truncate text-right font-medium text-stone-800">
                    {restrictions.disliked}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-stone-500">Мед. особенности</dt>
                  <dd className="max-w-[55%] truncate text-right font-medium text-stone-800">
                    {restrictions.medical}
                  </dd>
                </div>
              </dl>
              <Link
                href="/profile/nutrition"
                className="mt-3 inline-block text-xs font-semibold text-emerald-700"
              >
                Изменить в профиле питания
              </Link>
            </MenuPlannerSection>

            <MenuPlannerSection title="Что учтёт ПланАм">
              <ul className="space-y-2">
                {CHECKLIST_ITEMS.map((item) => (
                  <li
                    key={item.id}
                    className="flex items-center gap-2 text-sm text-stone-700"
                  >
                    <span
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs ${
                        checklist[item.id]
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-stone-100 text-stone-400"
                      }`}
                      aria-hidden
                    >
                      {checklist[item.id] ? "✓" : "·"}
                    </span>
                    {item.label}
                  </li>
                ))}
              </ul>
            </MenuPlannerSection>

            <MenuPlannerSection title="Текущий план">
              {hasPlan && selectedMenu ? (
                <>
                  <ul className="space-y-1.5 text-sm text-stone-600">
                    <li>Период: на сегодня</li>
                    <li>Персон: {personsCount}</li>
                    {selectedDate ? <li>Создан: {selectedDate}</li> : null}
                    <li>
                      Статус:{" "}
                      <span className="font-semibold text-emerald-700">
                        активен
                      </span>
                    </li>
                  </ul>
                  <p className="mt-2 font-semibold text-stone-900">
                    {selectedMenu.menu.title}
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <Link
                      href="/menu/current"
                      className="flex min-h-[40px] items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50 py-2 text-center text-sm font-semibold text-emerald-800"
                    >
                      Открыть план
                    </Link>
                    <button
                      type="button"
                      onClick={() => void handleGenerate()}
                      disabled={generating}
                      className="min-h-[40px] rounded-xl border border-stone-200 py-2 text-sm font-semibold text-stone-700"
                    >
                      Пересобрать
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-sm text-stone-600">Плана пока нет</p>
              )}
            </MenuPlannerSection>
          </>
        )}
      </main>

      {phase === "setup" ? (
        <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-stone-200/90 bg-white/95 px-4 py-3 backdrop-blur-md pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div className="mx-auto max-w-lg">
            <button
              type="button"
              disabled={generating || !initData}
              onClick={() => void handleGenerate()}
              className="w-full min-h-[48px] rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/40 disabled:opacity-50 active:scale-[0.99]"
            >
              {generating
                ? "Составляем план…"
                : hasPlan
                  ? "Составить новый план"
                  : "Составить план"}
            </button>
          </div>
        </div>
      ) : null}

      {previewMenu ? (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-stone-50">
          <div className="mx-auto max-w-lg px-4 py-4">
            <button
              type="button"
              onClick={() => setPreviewMenu(null)}
              className="text-sm font-semibold text-emerald-700"
            >
              ← Назад к выбору
            </button>
            <div className="mt-3">
              <MenuVariantCard
                menu={previewMenu}
                selected={false}
                onSelect={() => void handleSelect(previewMenu)}
                onReplace={() => {}}
                selecting={selecting}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
