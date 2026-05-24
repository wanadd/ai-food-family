"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { ApiRequestError } from "@/lib/api-errors";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuChooseVariants } from "@/components/menu/MenuChooseVariants";
import { MenuPlannerSection } from "@/components/menu/MenuPlannerSection";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { MenuWizardSteps } from "@/components/menu/MenuWizardSteps";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  buildChecklistItemStatuses,
  buildRestrictionsSummary,
} from "@/lib/menu/planner-summary";
import { maxWizardScreenIndex } from "@/lib/menu/wizard-steps";
import {
  type MenuGoalId,
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
  const [wizardStep, setWizardStep] = useState(0);
  const [wizardGoal, setWizardGoal] = useState<MenuGoalId | null>(null);
  const [goalStepError, setGoalStepError] = useState<string | null>(null);
  const [wizardDays, setWizardDays] = useState(7);
  const [wizardBudget, setWizardBudget] = useState("standard");
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
        setGoalStepError(null);
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

  const restrictions = buildRestrictionsSummary(profile);
  const isFamily = mode === "family";
  const effectivePersons = isFamily ? personsCount : 1;
  const checklistStatuses = buildChecklistItemStatuses(
    profile,
    effectivePersons,
    checklistPantry,
    isFamily,
  );
  const maxWizardStep = maxWizardScreenIndex(isFamily);
  const hasPlan = Boolean(selectedMenu?.menu);

  function changePlanMode(id: PlanModeId) {
    setPlanMode(id);
    savePlanMode(id);
  }

  function handleWizardContinue() {
    if (wizardStep === 0) {
      if (!wizardGoal) {
        setGoalStepError("Выберите цель для продолжения");
        return;
      }
      setGoalStepError(null);
    }
    if (wizardStep < maxWizardStep) {
      setWizardStep((s) => s + 1);
      return;
    }
    void handleGenerate();
  }

  async function handleGenerate() {
    if (!initData) {
      setError("Откройте приложение в Telegram и попробуйте снова.");
      return;
    }
    if (!wizardGoal) {
      setGoalStepError("Выберите цель для продолжения");
      setWizardStep(0);
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
          text = `${text} Дополнительная генерация спишет Амы с баланса.`;
        }
        setError(text.trim());
      } else {
        const msg =
          err instanceof Error ? err.message : "Не удалось создать меню. Попробуйте ещё раз.";
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
    <div
      className="min-h-screen bg-stone-50"
      style={{
        paddingBottom:
          "calc(4.75rem + env(safe-area-inset-bottom, 0px) + 5.25rem)",
      }}
    >
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
            {effectivePersons === 1
              ? "На 1 человека"
              : `На ${effectivePersons} человек`}
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
          <>
            {generateSuccess ? (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                <p className="font-semibold">Меню создано</p>
                <p className="mt-1">
                  Выберите вариант ниже или откройте план после сохранения.
                </p>
                <Link
                  href="/menu/current"
                  className="mt-2 inline-block font-semibold text-emerald-800"
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
          </>
        ) : (
          <>
            <MenuWizardSteps
              screenIndex={wizardStep}
              goal={wizardGoal}
              goalError={goalStepError}
              onGoalChange={(g) => {
                setWizardGoal(g);
                setGoalStepError(null);
              }}
              personsCount={effectivePersons}
              onPersonsChange={setPersonsCount}
              days={wizardDays}
              onDaysChange={setWizardDays}
              budget={wizardBudget}
              onBudgetChange={setWizardBudget}
              planMode={planMode}
              onPlanModeChange={changePlanMode}
              checklistStatuses={checklistStatuses}
              familyName={context?.family?.name}
              isFamily={isFamily}
            />
            {hasPlan && selectedMenu ? (
              <MenuPlannerSection title="Текущий план">
                <p className="text-sm font-semibold text-stone-900">
                  {selectedMenu.menu.title}
                </p>
                {selectedDate ? (
                  <p className="mt-1 text-xs text-stone-500">Создан: {selectedDate}</p>
                ) : null}
                <Link
                  href="/menu/current"
                  className="mt-3 inline-block text-sm font-semibold text-emerald-700"
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
          <div className="flex gap-2">
            {wizardStep > 0 ? (
              <button
                type="button"
                onClick={() => {
                  setGoalStepError(null);
                  setWizardStep((s) => s - 1);
                }}
                className="min-h-[48px] shrink-0 rounded-2xl border border-stone-200 px-4 text-sm font-semibold text-stone-700"
              >
                Назад
              </button>
            ) : null}
            <button
              type="button"
              disabled={generating || !initData}
              onClick={handleWizardContinue}
              className="w-full min-h-[48px] flex-1 rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/40 disabled:opacity-50"
            >
              {generating
                ? "Составляем…"
                : wizardStep < maxWizardStep
                  ? "Продолжить"
                  : "Сгенерировать меню"}
            </button>
          </div>
        </StickyBottomBar>
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
