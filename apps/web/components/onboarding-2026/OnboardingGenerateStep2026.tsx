"use client";

import { AiProcessLoading2026 } from "@/components/planam-2026/ui/AiProcessLoading2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";

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
  generating: "Подбираем блюда на неделю…",
  selecting: "Сохраняем план…",
  loading_preview: "Готовим превью…",
  error: "Не удалось завершить",
};

type OnboardingGenerateStep2026Props = {
  phase: GeneratePhase;
  errorMessage: string | null;
  onStart: () => void;
  onRetry: () => void;
};

export function OnboardingGenerateStep2026({
  phase,
  errorMessage,
  onStart,
  onRetry,
}: OnboardingGenerateStep2026Props) {
  const busy = phase !== "idle" && phase !== "error";
  const showAiLoader = phase === "generating" || phase === "selecting" || phase === "loading_preview";

  if (phase === "error") {
    return (
      <EmptyState2026
        title="План пока не создался"
        description={
          errorMessage ??
          "Проверьте сеть и попробуйте ещё раз — мы не показываем пустую загрузку."
        }
        actionLabel="Повторить"
        onAction={onRetry}
      />
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
            PLANAM подберёт блюда с учётом цели и ограничений. Обычно 15–40 секунд.
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
          Составить план
        </Button2026>
      ) : null}
    </div>
  );
}
