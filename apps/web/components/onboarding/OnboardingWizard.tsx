"use client";

import { useCallback, useEffect, useState } from "react";
import { useTelegram } from "@/components/TelegramProvider";

import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { OnboardingComplete } from "@/components/onboarding/OnboardingComplete";
import { ProgressBar } from "@/components/onboarding/ProgressBar";
import { StepContent } from "@/components/onboarding/StepContent";
import { StepNavigation } from "@/components/onboarding/StepNavigation";
import { fetchRemoteOnboarding, saveRemoteOnboarding } from "@/lib/onboarding/api";
import { ONBOARDING_STEPS, TOTAL_STEPS } from "@/lib/onboarding/steps";
import { loadLocalOnboarding, saveLocalOnboarding } from "@/lib/onboarding/storage";
import { INITIAL_ONBOARDING, type OnboardingData } from "@/lib/onboarding/types";

function mergeOnboarding(
  local: OnboardingData,
  remote: OnboardingData | null,
): OnboardingData {
  if (!remote) {
    return local;
  }

  if (remote.completed) {
    return remote;
  }

  if (remote.currentStep > local.currentStep) {
    return remote;
  }

  return local;
}

function canProceed(stepIndex: number, data: OnboardingData): boolean {
  const step = ONBOARDING_STEPS[stepIndex];
  if (!step) {
    return false;
  }

  switch (step.id) {
    case "welcome":
      return true;
    case "goals":
      return data.goals.length > 0;
    case "diets":
      return data.diets.length > 0;
    case "allergies":
      return data.allergies.length > 0;
    case "restrictions":
      return data.restrictions.length > 0;
    case "budget":
      return Boolean(data.budget);
    case "cookingTime":
      return Boolean(data.cookingTime);
  }

  return true;
}

export function OnboardingWizard() {
  const { initData } = useTelegram();
  const [data, setData] = useState<OnboardingData>(INITIAL_ONBOARDING);
  const [hydrated, setHydrated] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveHint, setSaveHint] = useState<string | null>(null);

  useEffect(() => {
    async function hydrate() {
      const local = loadLocalOnboarding();
      let merged = local;

      if (initData) {
        const remote = await fetchRemoteOnboarding(initData);
        merged = mergeOnboarding(local, remote);
      }

      setData(merged);
      saveLocalOnboarding(merged);
      setHydrated(true);
    }

    hydrate();
  }, [initData]);

  const persist = useCallback(async (next: OnboardingData) => {
    setData(next);
    saveLocalOnboarding(next);
    setSaveHint("Сохранено локально");

    if (!initData) {
      return;
    }

    setSaving(true);
    try {
      await saveRemoteOnboarding(initData, next);
      setSaveHint("Синхронизировано с сервером");
    } catch {
      setSaveHint("Не удалось синхронизировать — данные в браузере");
    } finally {
      setSaving(false);
    }
  }, [initData]);

  const patch = useCallback(
    (patchData: Partial<OnboardingData>) => {
      setData((current) => {
        const next = { ...current, ...patchData };
        saveLocalOnboarding(next);
        return next;
      });
    },
    [],
  );

  const step = ONBOARDING_STEPS[data.currentStep];
  const isLastStep = data.currentStep === TOTAL_STEPS - 1;
  const isWelcome = step?.id === "welcome";

  async function handleNext() {
    if (!step || !canProceed(data.currentStep, data)) {
      return;
    }

    if (isLastStep) {
      const completed: OnboardingData = {
        ...data,
        completed: true,
        currentStep: TOTAL_STEPS - 1,
      };
      await persist(completed);
      return;
    }

    const next: OnboardingData = {
      ...data,
      currentStep: data.currentStep + 1,
    };
    await persist(next);
  }

  async function handleBack() {
    if (data.currentStep === 0 || data.completed) {
      return;
    }

    const next: OnboardingData = {
      ...data,
      currentStep: data.currentStep - 1,
    };
    await persist(next);
  }

  if (!hydrated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-sm text-stone-500">
        Загрузка прогресса…
      </div>
    );
  }

  if (data.completed) {
    return <OnboardingComplete data={data} />;
  }

  if (!step) {
    return null;
  }

  const proceedAllowed = canProceed(data.currentStep, data);

  return (
    <div className="flex min-h-screen flex-col bg-[#fafaf9]">
      <header className="border-b border-stone-200/80 bg-[#fafaf9]/95 px-5 pb-4 pt-6 backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
          AI Food Family
        </p>
        <ProgressBar current={data.currentStep} total={TOTAL_STEPS} />
      </header>

      <main className="mx-auto flex w-full max-w-lg flex-1 flex-col px-5 py-8">
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">
          {step.title}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-stone-500">
          {step.subtitle}
        </p>

        <div className="mt-8 flex-1">
          <StepContent stepId={step.id} data={data} onChange={patch} />
        </div>

        {!proceedAllowed && !isWelcome ? (
          <p className="mt-4 text-xs text-amber-700">
            Выберите хотя бы один вариант, чтобы продолжить
          </p>
        ) : null}

        {saveHint ? (
          <p className="mt-3 text-center text-xs text-stone-400">{saveHint}</p>
        ) : null}
      </main>

      <div className="px-5 pb-2">
        <BottomBackButton className="px-0" />
      </div>

      <footer className="sticky bottom-0 border-t border-stone-200/80 bg-white/95 px-5 py-4 backdrop-blur">
        <StepNavigation
          canGoBack={data.currentStep > 0}
          canGoNext={proceedAllowed}
          isLastStep={isLastStep}
          isWelcome={isWelcome}
          saving={saving}
          onBack={handleBack}
          onNext={handleNext}
        />
        {!proceedAllowed && !isWelcome ? (
          <p className="mt-2 text-center text-[11px] text-stone-400">
            Кнопка «Далее» станет активной после выбора
          </p>
        ) : null}
      </footer>
    </div>
  );
}
