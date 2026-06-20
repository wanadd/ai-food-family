"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { OnboardingGenerateStep2026 } from "@/components/onboarding-2026/OnboardingGenerateStep2026";
import type { GeneratePhase } from "@/components/onboarding-2026/OnboardingGenerateStep2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { useTelegram } from "@/components/TelegramProvider";
import { ApiRequestError } from "@/lib/api-errors";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { generateMenus, selectMenu, fetchSelectedMenu } from "@/lib/menu/api";
import {
  MENU_DAY_OPTIONS,
  MENU_GOAL_OPTIONS,
  PLAN_MODE_OPTIONS,
  type MenuGoalId,
  type PlanModeId,
} from "@/lib/menu/planner-options";
import { loadPlanMode, savePlanMode } from "@/lib/menu/planner-storage";
import type { MenuVariant } from "@/lib/menu/types";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import { fetchPantry } from "@/lib/pantry/api";
import { cn } from "@/lib/planam/cn";
import { VARIANT_LABELS } from "@/lib/menu/labels";

type WizardStep = "days" | "prefs" | "generate" | "choose";

export function PlanGenerate2026() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [step, setStep] = useState<WizardStep>("days");
  const [planDays, setPlanDays] = useState<number>(5);
  const [goal, setGoal] = useState<MenuGoalId | null>(null);
  const [planMode, setPlanMode] = useState<PlanModeId>("healthy");
  const [usePantry, setUsePantry] = useState(true);
  const [pantryCount, setPantryCount] = useState(0);
  const [pantryList, setPantryList] = useState<Awaited<ReturnType<typeof fetchPantry>> | null>(null);
  const [phase, setPhase] = useState<GeneratePhase>("idle");
  const [genError, setGenError] = useState<string | null>(null);
  const [variants, setVariants] = useState<MenuVariant[]>([]);
  const [selecting, setSelecting] = useState(false);

  const personsCount = useMemo(() => {
    if (mode === "family" && context?.family) {
      return context.family.members_count ?? context.family.members.length ?? 1;
    }
    return 1;
  }, [mode, context]);

  useEffect(() => {
    if (!initData || modeLoading) {
      return;
    }
    void (async () => {
      const [profile, pantry] = await Promise.all([
        fetchNutritionProfile(initData).catch(() => null),
        fetchPantry(initData, mode).catch(() => null),
      ]);
      const ng = profile?.nutrition_goal as MenuGoalId | undefined;
      if (ng && MENU_GOAL_OPTIONS.some((o) => o.value === ng)) {
        setGoal(ng);
      }
      const stored = loadPlanMode();
      if (
        stored &&
        PLAN_MODE_OPTIONS.some((o) => o.value === stored)
      ) {
        setPlanMode(stored as PlanModeId);
      }
      setPantryList(pantry);
      setPantryCount(pantry?.active_count ?? 0);
    })();
  }, [initData, mode, modeLoading]);

  const runGenerate = useCallback(async () => {
    if (!initData || !goal) {
      return;
    }
    setPhase("generating");
    setGenError(null);
    try {
      savePlanMode(planMode);
      const result = await generateMenus(initData, mode, {
        mode,
        goal,
        personsCount: personsCount,
        planDays,
        planMode: usePantry ? "use_pantry" : planMode,
        wizardBudget: "standard",
        pantry: usePantry ? pantryList : null,
      });
      setVariants(result.menus ?? []);
      setStep("choose");
      setPhase("idle");
    } catch (err) {
      setPhase("error");
      setGenError(
        err instanceof ApiRequestError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Не удалось создать меню",
      );
    }
  }, [initData, mode, goal, planMode, planDays, personsCount, usePantry, pantryList]);

  async function handleSelect(menu: MenuVariant) {
    if (!initData) {
      return;
    }
    setSelecting(true);
    try {
      await selectMenu(initData, mode, menu);
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      router.replace(`${PLAN_PATHS.today}?saved=1`);
    } catch (err) {
      setGenError(
        err instanceof Error ? err.message : "Не удалось сохранить план",
      );
    } finally {
      setSelecting(false);
    }
  }

  if (step === "choose") {
    return (
      <div className="space-y-4 px-4 pb-8 pt-4">
        <h1 className="pa26-page-title">Выберите план</h1>
        <p className="pa26-body text-pa-muted">
          Один вариант станет активным, список покупок обновится автоматически.
        </p>
        {variants.length === 0 ? (
          <EmptyState2026
            title="Вариантов нет"
            actionLabel="Повторить"
            onAction={() => {
              setStep("generate");
              void runGenerate();
            }}
          />
        ) : (
          variants.map((menu) => {
            const meta = VARIANT_LABELS[menu.variant];
            return (
              <Card2026 key={menu.variant}>
                <p className="pa26-card-title">
                  {meta.emoji} {menu.title}
                </p>
                <p className="pa26-caption mt-1 text-pa-muted">{menu.tagline}</p>
                <Button2026
                  variant="primary"
                  className="mt-3 w-full"
                  loading={selecting}
                  onClick={() => void handleSelect(menu)}
                >
                  Выбрать
                </Button2026>
              </Card2026>
            );
          })
        )}
      </div>
    );
  }

  if (step === "generate") {
    return (
      <div className="px-4 pb-8 pt-4">
        <OnboardingGenerateStep2026
          phase={phase}
          errorMessage={genError}
          onStart={() => void runGenerate()}
          onRetry={() => void runGenerate()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 px-4 pb-8 pt-4">
      <h1 className="pa26-page-title">Новый план</h1>

      {step === "days" ? (
        <>
          <p className="pa26-body text-pa-muted">На сколько дней составить меню?</p>
          <div className="flex flex-wrap gap-2">
            {MENU_DAY_OPTIONS.filter((d) => [3, 5, 7].includes(d)).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setPlanDays(d)}
                className={cn(
                  "rounded-control border px-4 py-2.5 pa26-body font-semibold",
                  planDays === d
                    ? "border-sage-500 bg-sage-500 text-white dark:bg-sage-400"
                    : "border-pa-border bg-pa-surface",
                )}
              >
                {d} дн.
              </button>
            ))}
          </div>
          <Button2026 variant="primary" className="w-full" onClick={() => setStep("prefs")}>
            Далее
          </Button2026>
        </>
      ) : null}

      {step === "prefs" ? (
        <>
          <p className="pa26-section-title">Цель питания</p>
          <div className="flex flex-wrap gap-2">
            {MENU_GOAL_OPTIONS.map((o) => (
              <button
                key={o.value}
                type="button"
                onClick={() => setGoal(o.value)}
                className={cn(
                  "rounded-pill border px-3 py-1.5 pa26-micro font-semibold",
                  goal === o.value
                    ? "bg-sage-500 text-white dark:bg-sage-400"
                    : "border-pa-border bg-pa-surface text-pa-muted",
                )}
              >
                {o.label}
              </button>
            ))}
          </div>

          <p className="pa26-section-title mt-4">Режим плана</p>
          <div className="space-y-2">
            {PLAN_MODE_OPTIONS.slice(0, 4).map((o) => (
              <button
                key={o.value}
                type="button"
                onClick={() => setPlanMode(o.value)}
                className={cn(
                  "w-full rounded-card border px-4 py-3 text-left",
                  planMode === o.value
                    ? "border-sage-400 bg-sage-50 dark:bg-sage-700/20"
                    : "border-pa-border bg-pa-surface",
                )}
              >
                <span className="pa26-card-title">{o.label}</span>
                <span className="pa26-caption block text-pa-muted">{o.hint}</span>
              </button>
            ))}
          </div>

          <label className="mt-4 flex items-center gap-3 rounded-card border border-pa-border bg-pa-surface px-4 py-3">
            <input
              type="checkbox"
              checked={usePantry}
              onChange={(e) => setUsePantry(e.target.checked)}
              className="size-5 rounded border-pa-border"
            />
            <span className="pa26-body">
              Учесть запасы ({pantryCount} продуктов)
            </span>
          </label>

          <div className="flex gap-2 pt-2">
            <Button2026 variant="ghost" className="flex-1" onClick={() => setStep("days")}>
              Назад
            </Button2026>
            <Button2026
              variant="primary"
              className="flex-1"
              disabled={!goal}
              onClick={() => setStep("generate")}
            >
              Составить план
            </Button2026>
          </div>
        </>
      ) : null}
    </div>
  );
}
