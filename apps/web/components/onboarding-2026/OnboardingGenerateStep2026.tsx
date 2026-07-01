"use client";

import { AiProcessLoading2026 } from "@/components/planam-2026/ui/AiProcessLoading2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { formatMenuDuration } from "@/lib/menu/duration-options";

export type GeneratePhase =
  | "idle"
  | "saving_profile"
  | "generating"
  | "selecting"
  | "loading_preview"
  | "error";

const PHASE_LABELS: Record<GeneratePhase, string> = {
  idle: "Готовы составить ваш первый план",
  saving_profile: "Сохраняем предпочтения…",
  generating: "Подбираем блюда…",
  selecting: "Сохраняем план…",
  loading_preview: "Готовим превью…",
  error: "Не удалось завершить",
};

type OnboardingGenerateStep2026Props = {
  phase: GeneratePhase;
  errorMessage: string | null;
  planDays: number;
  onStart: () => void;
  onRetry: () => void;
  onContinueWithoutMenu: () => void;
};

export function OnboardingGenerateStep2026({
  phase,
  errorMessage,
  planDays,
  onStart,
  onRetry,
  onContinueWithoutMenu,
}: OnboardingGenerateStep2026Props) {
  const busy = phase !== "idle" && phase !== "error";
  const showAiLoader = phase === "generating" || phase === "selecting" || phase === "loading_preview";
  const duration = formatMenuDuration(planDays);

  if (phase === "error") {
    return (
      <Card2026 className="space-y-4">
        <div>
          <p className="pa26-section-title">Не получилось собрать меню с первого раза</p>
          <p className="pa26-body mt-2 text-pa-muted">
            {errorMessage ??
              "Можно попробовать ещё раз или открыть приложение и собрать меню позже."}
          </p>
        </div>
        <div className="space-y-2">
          <Button2026 variant="primary" size="wide" onClick={onRetry}>
            Попробовать снова
          </Button2026>
          <Button2026 variant="secondary" size="wide" onClick={onContinueWithoutMenu}>
            Открыть приложение без меню
          </Button2026>
        </div>
      </Card2026>
    );
  }

  return (
    <div className="space-y-4">
      {showAiLoader ? (
        <AiProcessLoading2026 active />
      ) : (
        <Card2026>
          <p className="pa26-section-title">Создаём ваш план</p>
          <p className="pa26-body mt-2 text-pa-muted">
            PLANAM подберёт меню на {duration} с учётом цели и ограничений.
            Обычно 15–40 секунд.
          </p>
          {busy ? (
            <p className="pa26-caption mt-4 font-medium text-sage-700 dark:text-sage-300">
              {PHASE_LABELS[phase]}
            </p>
          ) : null}
        </Card2026>
      )}
      {!busy ? (
        <Button2026 variant="primary" size="wide" onClick={onStart}>
          Собрать меню на {duration}
        </Button2026>
      ) : null}
    </div>
  );
}
