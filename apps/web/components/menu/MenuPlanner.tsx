"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { ApiRequestError } from "@/lib/api-errors";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuChooseVariants } from "@/components/menu/MenuChooseVariants";
import { MenuPlannerSection } from "@/components/menu/MenuPlannerSection";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  buildChecklistItemStatuses,
} from "@/lib/menu/planner-summary";
import {
  CHECKLIST_ADD_LINKS,
  CHECKLIST_ITEMS,
  MENU_BUDGET_OPTIONS,
  MENU_DAY_OPTIONS,
  MENU_GOAL_OPTIONS,
  PLAN_MODE_OPTIONS,
  type MenuGoalId,
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
import type { SelectedMenu, MenuVariant } from "@/lib/menu/types";

type Phase = "setup" | "choose";

export function MenuPlanner() {
  const router = useRouter();
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
  const [generateSuccess, setGenerateSuccess] = useState(false);

  const [personsCount, setPersonsCount] = useState(1);
  const [planMode, setPlanMode] = useState<PlanModeId>("healthy");
  const [wizardGoal, setWizardGoal] = useState<MenuGoalId | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [wizardDays, setWizardDays] = useState(7);
  const [wizardBudget, setWizardBudget] = useState("standard");
  const [advancedOpen, setAdvancedOpen] = useState(false);
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
      const ng = nutrition?.nutrition_goal as MenuGoalId | undefined;
      if (ng && ["maintain", "lose", "gain", "healthy", "sport", "kids"].includes(ng)) {
        setWizardGoal(ng);
        setGoalError(null);
      }
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

  const isFamily = mode === "family";
  const effectivePersons = isFamily ? personsCount : 1;
  const checklistStatuses = buildChecklistItemStatuses(
    profile,
    effectivePersons,
    checklistPantry,
    isFamily,
  );
  const hasPlan = Boolean(selectedMenu?.menu);

  const accountedItems = CHECKLIST_ITEMS.filter(
    (item) => (isFamily || item.id !== "persons") && checklistStatuses[item.id] === "included",
  );
  const missingItems = CHECKLIST_ITEMS.filter(
    (item) => (isFamily || item.id !== "persons") && checklistStatuses[item.id] !== "included",
  );

  function changePlanMode(id: PlanModeId) {
    setPlanMode(id);
    savePlanMode(id);
  }

  async function handleGenerate() {
    if (!initData) {
      setError("Откройте приложение в Telegram и попробуйте снова.");
      return;
    }
    if (!wizardGoal) {
      setGoalError("Выберите цель — ПланАм поймёт, что для вас составить");
      return;
    }
    setGenerating(true);
    setError(null);
    setGenerateSuccess(false);
    try {
      const result = await generateMenus(initData, mode, {
        mode,
        goal: wizardGoal,
        personsCount: effectivePersons,
        planDays: wizardDays,
        planMode,
        wizardBudget,
        pantry: checklistPantry,
      });
      setGeneratedMenus(result.menus);
      setGenerateSuccess(true);
      setPhase("choose");
    } catch (err) {
      if (err instanceof ApiRequestError) {
        let text = err.message;
        if (err.code === "menu_generation_limit" && err.canPayWithAms) {
          text = `${text} Если хотите продолжить — повторная генерация спишет Амы с баланса.`;
        }
        setError(text.trim());
      } else {
        const msg =
          err instanceof Error
            ? err.message
            : "Не получилось составить меню. Попробуйте ещё раз через минуту.";
        setError(msg);
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
      await selectMenu(initData, mode, menu);
      router.push("/menu/current?saved=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить план");
    } finally {
      setSelecting(false);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-graphite-600">
          План питания доступен в Telegram Mini App.
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-sage-700">
          На главную
        </Link>
      </div>
    );
  }

  if (loading || modeLoading) {
    return (
      <div className="min-h-screen bg-cream">
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
    <div
      className="min-h-screen bg-cream"
      style={{
        paddingBottom:
          "calc(4.75rem + env(safe-area-inset-bottom, 0px) + 5.25rem)",
      }}
    >
      <header className="border-b border-cream-border bg-cream-surface px-4 py-4">
        <div className="mx-auto max-w-lg">
          <Link href="/menu" className="text-sm font-semibold text-sage-700">
            ← Меню
          </Link>
          {phase === "choose" ? (
            <button
              type="button"
              onClick={() => {
                setPhase("setup");
                setGeneratedMenus([]);
              }}
              className="mt-2 block text-sm font-semibold text-sage-700"
            >
              ← Назад к настройкам
            </button>
          ) : null}
          <h1 className="mt-1 text-xl font-bold text-graphite-900">Составить меню</h1>
          <p className="mt-0.5 text-sm text-graphite-500">
            {effectivePersons === 1
              ? "На 1 человека"
              : `На ${effectivePersons} человек`}
            {" · "}
            финальный план выбираете вы
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        {error ? (
          <div className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <p>{error}</p>
            {error.includes("Лимит") || error.includes("Пробный") ? (
              <Link
                href="/subscription"
                className="mt-2 inline-block font-semibold text-sage-800"
              >
                Тариф и Амы →
              </Link>
            ) : null}
          </div>
        ) : null}

        {phase === "choose" ? (
          <>
            {generateSuccess ? (
              <div className="rounded-control border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-graphite-900">
                <p className="font-semibold">Меню готово</p>
                <p className="mt-1">
                  Выберите вариант ниже. Если что-то не подходит — любое блюдо
                  можно заменить уже в активном плане.
                </p>
                <Link
                  href="/menu/current"
                  className="mt-2 inline-block font-semibold text-sage-800"
                >
                  Открыть план →
                </Link>
              </div>
            ) : null}
            <MenuChooseVariants
              menus={generatedMenus}
              selecting={selecting}
              onSelect={(menu) => void handleSelect(menu)}
              onPreview={setPreviewMenu}
            />
            <section className="pa-card p-4">
              <h2 className="text-sm font-bold text-graphite-900">
                Свой вариант
              </h2>
              <p className="mt-1 text-sm text-graphite-600">
                Если ни один не подошёл — выберите ближайший, а потом замените
                любое блюдо в плане под себя. ПланАм пересчитает покупки.
              </p>
            </section>
          </>
        ) : (
          <>
            <MenuPlannerSection title="Цель">
              <div className="grid gap-2">
                {MENU_GOAL_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => {
                      setWizardGoal(opt.value);
                      setGoalError(null);
                    }}
                    className={`rounded-control border px-4 py-3 text-left text-sm font-medium ${
                      wizardGoal === opt.value
                        ? "border-sage-500 bg-sage-50 text-sage-900"
                        : "border-cream-border bg-cream-surface text-graphite-800"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              {goalError ? (
                <p className="mt-3 text-sm font-medium text-red-700" role="alert">
                  {goalError}
                </p>
              ) : null}
            </MenuPlannerSection>

            <MenuPlannerSection title="На сколько дней">
              <div className="grid grid-cols-3 gap-2">
                {MENU_DAY_OPTIONS.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setWizardDays(d)}
                    className={`min-h-[44px] rounded-control border text-sm font-semibold ${
                      wizardDays === d
                        ? "border-sage-500 bg-sage-50 text-sage-900"
                        : "border-cream-border bg-cream-surface"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </MenuPlannerSection>

            <section className="pa-card p-4">
              <h2 className="text-sm font-bold text-graphite-900">ПланАм учтёт</h2>
              {accountedItems.length > 0 ? (
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {accountedItems.map((item) => (
                    <li
                      key={item.id}
                      className="rounded-full bg-sage-100 px-2.5 py-0.5 text-xs font-semibold text-sage-800"
                    >
                      {item.label}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-graphite-600">
                  Пока опираемся на цель и количество дней. Можно дополнить
                  профиль ниже — план станет точнее.
                </p>
              )}
              {missingItems.length > 0 ? (
                <p className="mt-3 text-xs text-graphite-500">
                  Можно дополнить:{" "}
                  {missingItems
                    .map((item) => {
                      const href = CHECKLIST_ADD_LINKS[item.id];
                      return href ? (
                        <Link
                          key={item.id}
                          href={href}
                          className="font-semibold text-sage-700"
                        >
                          {item.label}
                        </Link>
                      ) : (
                        <span key={item.id}>{item.label}</span>
                      );
                    })
                    .reduce<ReactNode[]>((acc, node, idx) => {
                      if (idx > 0) acc.push(", ");
                      acc.push(node);
                      return acc;
                    }, [])}
                  .
                </p>
              ) : null}
            </section>

            <details
              className="group pa-card"
              open={advancedOpen}
              onToggle={(e) => setAdvancedOpen((e.target as HTMLDetailsElement).open)}
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-3.5 text-sm font-semibold text-graphite-900">
                <span>Настроить подробнее</span>
                <span
                  aria-hidden
                  className="text-graphite-400 transition group-open:rotate-180"
                >
                  ▾
                </span>
              </summary>

              <div className="space-y-5 border-t border-cream-border px-4 py-4">
                {isFamily ? (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
                      Количество человек
                    </p>
                    {context?.family?.name ? (
                      <p className="mt-1 text-xs text-graphite-500">
                        Семья: {context.family.name}
                      </p>
                    ) : null}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                        <button
                          key={n}
                          type="button"
                          onClick={() => setPersonsCount(n)}
                          className={`min-h-[40px] min-w-[40px] rounded-control border text-sm font-semibold ${
                            personsCount === n
                              ? "border-sage-500 bg-sage-50 text-sage-900"
                              : "border-cream-border bg-cream-surface"
                          }`}
                        >
                          {n}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
                    Бюджет
                  </p>
                  <div className="mt-2 grid gap-2">
                    {MENU_BUDGET_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setWizardBudget(opt.value)}
                        className={`rounded-control border px-3 py-2.5 text-left text-sm font-medium ${
                          wizardBudget === opt.value
                            ? "border-sage-500 bg-sage-50 text-sage-900"
                            : "border-cream-border bg-cream-surface text-graphite-800"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
                    Режим плана
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {PLAN_MODE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => changePlanMode(opt.value)}
                        className={`rounded-full border px-3 py-1.5 text-xs font-medium ${
                          planMode === opt.value
                            ? "border-sage-500 bg-sage-50 font-semibold"
                            : "border-cream-border"
                        }`}
                        title={opt.hint}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <p className="mt-1.5 text-[11px] text-graphite-500">
                    {PLAN_MODE_OPTIONS.find((o) => o.value === planMode)?.hint}
                  </p>
                </div>

                {missingItems.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
                      Что можно дополнить в профиле
                    </p>
                    <ul className="mt-2 space-y-1.5">
                      {missingItems.map((item) => {
                        const href = CHECKLIST_ADD_LINKS[item.id];
                        return (
                          <li
                            key={item.id}
                            className="flex items-center justify-between gap-2 text-sm"
                          >
                            <span className="text-graphite-700">{item.label}</span>
                            {href ? (
                              <Link
                                href={href}
                                className="shrink-0 rounded-full bg-cream-deep px-2.5 py-0.5 text-xs font-semibold text-sage-800"
                              >
                                Дополнить
                              </Link>
                            ) : (
                              <span className="shrink-0 rounded-full bg-cream-deep px-2.5 py-0.5 text-xs text-graphite-500">
                                нет
                              </span>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ) : null}
              </div>
            </details>

            {hasPlan && selectedMenu ? (
              <MenuPlannerSection title="Текущий план">
                <p className="text-sm font-semibold text-graphite-900">
                  {selectedMenu.menu.title}
                </p>
                {selectedDate ? (
                  <p className="mt-1 text-xs text-graphite-500">Создан: {selectedDate}</p>
                ) : null}
                <Link
                  href="/menu/current"
                  className="mt-3 inline-block text-sm font-semibold text-sage-700"
                >
                  Открыть план →
                </Link>
              </MenuPlannerSection>
            ) : null}
          </>
        )}
      </main>

      {phase === "setup" ? (
        <StickyBottomBar>
          <button
            type="button"
            disabled={generating || !initData}
            onClick={handleGenerate}
            className="pa-btn-primary w-full min-h-[48px] py-3.5 text-base disabled:opacity-50"
          >
            {generating ? "Составляем…" : "Сгенерировать меню"}
          </button>
        </StickyBottomBar>
      ) : null}

      {previewMenu ? (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-cream">
          <div className="mx-auto max-w-lg px-4 py-4">
            <button
              type="button"
              onClick={() => setPreviewMenu(null)}
              className="text-sm font-semibold text-sage-700"
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
