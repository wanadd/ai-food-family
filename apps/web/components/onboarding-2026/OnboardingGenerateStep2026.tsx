"use client";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";

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
      <Card2026>
        <p className="pa26-section-title">Создаём ваш план</p>
        <p className="pa26-body mt-2 text-pa-muted">
          ПланАм подберёт блюда с учётом цели и ограничений. Это реальный запрос к
          серверу — обычно 15–40 секунд.
        </p>
        {busy ? (
          <div className="mt-4 space-y-3">
            <p className="pa26-caption font-medium text-sage-700 dark:text-sage-300">
              {PHASE_LABELS[phase]}
            </p>
            <Skeleton2026 variant="rect" aspectRatio="16/9" />
            <Skeleton2026 variant="text" className="max-w-[70%]" />
          </div>
        ) : null}
      </Card2026>
      {!busy ? (
        <Button2026 variant="primary" size="wide" onClick={onStart}>
          Составить план
        </Button2026>
      ) : null}
    </div>
  );
}
