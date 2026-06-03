"use client";

import { useCallback, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  OnboardingChipGrid2026,
  OnboardingMultiChip2026,
} from "@/components/onboarding-2026/OnboardingChipGrid2026";
import {
  OnboardingGenerateStep2026,
  type GeneratePhase,
} from "@/components/onboarding-2026/OnboardingGenerateStep2026";
import { OnboardingProgress2026 } from "@/components/onboarding-2026/OnboardingProgress2026";
import { OnboardingWowReveal2026 } from "@/components/onboarding-2026/OnboardingWowReveal2026";
import { useTelegram } from "@/components/TelegramProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { enrichTodayMeals } from "@/lib/home/home-2026-data";
import { generateMenus, selectMenu } from "@/lib/menu/api";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuVariant } from "@/lib/menu/types";
import {
  ALLERGY_CHIPS,
  DIET_CHIPS,
  GOAL_OPTIONS,
  INITIAL_WIZARD_STATE,
  mapWhoToPersons,
  mapWizardToNutrition,
  mapWizardToProfilePatch,
  RESTRICTION_OPTIONS,
  WHO_OPTIONS,
  type OnboardingWizardState,
} from "@/lib/onboarding-2026/config";
import { markWowComplete } from "@/lib/planam/onboarding-gate";
import {
  fetchNutritionProfile,
  saveNutritionProfile,
} from "@/lib/nutrition-profile/api";
import { INITIAL_NUTRITION_PROFILE } from "@/lib/nutrition-profile/types";
import { ApiRequestError } from "@/lib/api-errors";

function pickVariant(menus: MenuVariant[]): MenuVariant | null {
  if (!menus.length) return null;
  return (
    menus.find((m) => m.variant === "balanced") ??
    menus.find((m) => m.variant === "quick") ??
    menus[0]
  );
}

export function Onboarding2026Flow() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { overview: subscription, ensureLoaded } = useSubscriptionOverview();

  const [step, setStep] = useState(1);
  const [wizard, setWizard] = useState<OnboardingWizardState>(INITIAL_WIZARD_STATE);
  const [generatePhase, setGeneratePhase] = useState<GeneratePhase>("idle");
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [wowMeals, setWowMeals] = useState<ReturnType<typeof enrichTodayMeals>>([]);
  const [menuTitle, setMenuTitle] = useState<string | null>(null);

  const canNext = (() => {
    if (step === 1) return wizard.who != null;
    if (step === 2) return wizard.goal != null;
    if (step === 3) {
      if (wizard.restriction === "allergies") return wizard.allergyTags.length > 0;
      if (wizard.restriction === "diet") return wizard.dietTags.length > 0;
      return wizard.restriction != null;
    }
    return true;
  })();

  const runGenerate = useCallback(async () => {
    if (!initData || !wizard.who || !wizard.goal || wizard.restriction == null) {
      return;
    }

    setGenerateError(null);
    const { nutrition_goal, plan_mode } = mapWizardToNutrition(wizard);
    const persons = mapWhoToPersons(wizard.who);

    try {
      setGeneratePhase("saving_profile");
      const existing = await fetchNutritionProfile(initData).catch(
        () => INITIAL_NUTRITION_PROFILE,
      );
      await saveNutritionProfile(initData, {
        ...existing,
        ...mapWizardToProfilePatch(wizard),
      });
      invalidateCache("nutrition-profile");

      setGeneratePhase("generating");
      const result = await generateMenus(initData, mode, {
        mode,
        goal: nutrition_goal,
        personsCount: persons,
        planDays: 5,
        planMode: plan_mode,
        wizardBudget: "standard",
        pantry: null,
      });

      const variant = pickVariant(result.menus);
      if (!variant) {
        throw new Error("Сервер не вернул варианты меню");
      }

      setGeneratePhase("selecting");
      await selectMenu(initData, mode, variant);
      invalidateCache("menu-overview");
      invalidateCache("selected-menu");

      setGeneratePhase("loading_preview");
      void ensureLoaded();
      const overview = await fetchMenuOverview(initData, mode);
      setWowMeals(enrichTodayMeals(overview));
      setMenuTitle(overview.plan_summary.menu_title ?? variant.title);
      setGeneratePhase("idle");
      setStep(5);
    } catch (err) {
      setGeneratePhase("error");
      if (err instanceof ApiRequestError) {
        setGenerateError(err.message);
      } else {
        setGenerateError(
          err instanceof Error ? err.message : "Не удалось создать план",
        );
      }
    }
  }, [initData, mode, wizard, ensureLoaded]);

  const handleStartDay = () => {
    markWowComplete();
    invalidateCache("menu-overview");
    router.replace("/");
  };

  const handleNext = () => {
    if (step < 3) {
      setStep((s) => s + 1);
      return;
    }
    if (step === 3) {
      setStep(4);
      return;
    }
  };

  const handleBack = () => {
    if (step > 1 && step < 5) {
      setStep((s) => s - 1);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col">
      <OnboardingProgress2026 step={step} />
      <div className="flex-1 px-4 pb-8">
        {step === 1 ? (
          <StepShell
            title="Кто будет пользоваться?"
            subtitle="Один тап — без длинной анкеты"
          >
            <OnboardingChipGrid2026
              options={WHO_OPTIONS}
              value={wizard.who}
              onChange={(who) => setWizard((w) => ({ ...w, who }))}
              columns={2}
            />
          </StepShell>
        ) : null}

        {step === 2 ? (
          <StepShell title="Главная цель" subtitle="ПланАм подстроит меню под вас">
            <OnboardingChipGrid2026
              options={GOAL_OPTIONS}
              value={wizard.goal}
              onChange={(goal) => setWizard((w) => ({ ...w, goal }))}
            />
          </StepShell>
        ) : null}

        {step === 3 ? (
          <StepShell title="Ограничения" subtitle="Учтём при подборе блюд">
            <OnboardingChipGrid2026
              options={RESTRICTION_OPTIONS}
              value={wizard.restriction}
              onChange={(restriction) =>
                setWizard((w) => ({
                  ...w,
                  restriction,
                  allergyTags: restriction === "allergies" ? w.allergyTags : [],
                  dietTags: restriction === "diet" ? w.dietTags : [],
                }))
              }
              columns={2}
            />
            {wizard.restriction === "allergies" ? (
              <div className="mt-4">
                <p className="pa26-caption mb-2 text-pa-muted">Выберите аллергены</p>
                <OnboardingMultiChip2026
                  options={ALLERGY_CHIPS}
                  selected={wizard.allergyTags}
                  onToggle={(tag) =>
                    setWizard((w) => ({
                      ...w,
                      allergyTags: w.allergyTags.includes(tag)
                        ? w.allergyTags.filter((t) => t !== tag)
                        : [...w.allergyTags, tag],
                    }))
                  }
                />
              </div>
            ) : null}
            {wizard.restriction === "diet" ? (
              <div className="mt-4">
                <p className="pa26-caption mb-2 text-pa-muted">Тип питания</p>
                <OnboardingMultiChip2026
                  options={DIET_CHIPS}
                  selected={wizard.dietTags}
                  onToggle={(tag) =>
                    setWizard((w) => ({
                      ...w,
                      dietTags: w.dietTags.includes(tag)
                        ? w.dietTags.filter((t) => t !== tag)
                        : [...w.dietTags, tag],
                    }))
                  }
                />
              </div>
            ) : null}
            {wizard.restriction === "medical" ? (
              <p className="pa26-caption mt-4 text-pa-muted">
                Учтём ограничения при составлении — без дополнительных форм.
              </p>
            ) : null}
          </StepShell>
        ) : null}

        {step === 4 ? (
          <StepShell title="Ваш первый план" subtitle="Реальная генерация на сервере">
            <OnboardingGenerateStep2026
              phase={generatePhase}
              errorMessage={generateError}
              onStart={() => void runGenerate()}
              onRetry={() => {
                setGeneratePhase("idle");
                void runGenerate();
              }}
            />
          </StepShell>
        ) : null}

        {step === 5 ? (
          <OnboardingWowReveal2026
            meals={wowMeals}
            menuTitle={menuTitle}
            amaBalance={subscription?.ama_balance ?? null}
            onStartDay={handleStartDay}
          />
        ) : null}
      </div>

      {step >= 1 && step <= 3 ? (
        <footer className="flex gap-2 border-t border-pa-border bg-pa-surface px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
          {step > 1 ? (
            <Button2026 variant="ghost" className="flex-1" onClick={handleBack}>
              Назад
            </Button2026>
          ) : (
            <div className="flex-1" />
          )}
          <Button2026
            variant="primary"
            className="flex-[2]"
            disabled={!canNext}
            onClick={handleNext}
          >
            Далее
          </Button2026>
        </footer>
      ) : null}
    </div>
  );
}

function StepShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div>
      <h1 className="pa26-page-title">{title}</h1>
      <p className="pa26-body mt-1 text-pa-muted">{subtitle}</p>
      <div className="mt-6">{children}</div>
    </div>
  );
}
