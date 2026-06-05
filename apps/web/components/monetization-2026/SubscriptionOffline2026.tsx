"use client";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { buildMiniAppUrl } from "@/lib/telegram";

const PLUS_BENEFITS = [
  "AI-меню на неделю",
  "Список покупок из меню",
  "Учёт остатков",
  "Семейный доступ",
  "AI-нутрициолог",
] as const;

type SubscriptionOffline2026Props = {
  onRetry?: () => void;
};

export function SubscriptionOffline2026({ onRetry }: SubscriptionOffline2026Props) {
  const { isTelegram } = useTelegram();
  const { showToast } = useToast();
  const miniAppUrl = buildMiniAppUrl();

  function handleOpenTelegram() {
    if (isTelegram) {
      showToast("Вы уже в Telegram Mini App");
      return;
    }
    if (miniAppUrl && typeof window !== "undefined") {
      window.open(miniAppUrl, "_blank", "noopener,noreferrer");
      return;
    }
    showToast("Оплата доступна в Telegram Mini App");
  }

  return (
    <div className="space-y-4 px-4 pb-8 pt-2">
      <div>
        <h1 className="pa26-page-title">Подписка</h1>
        <p className="pa26-caption mt-1 text-pa-muted">
          Тарифы и возможности PLANAM
        </p>
      </div>

      <Card2026>
        <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
          Текущий статус
        </p>
        <p className="pa26-card-title mt-1">Сейчас: базовый доступ</p>
      </Card2026>

      <Card2026 className="border-sage-200 bg-sage-50/40 dark:border-sage-700/40 dark:bg-sage-700/15">
        <p className="pa26-card-title">PLANAM Plus</p>
        <ul className="mt-3 space-y-1.5">
          {PLUS_BENEFITS.map((benefit) => (
            <li key={benefit} className="pa26-caption text-pa-muted">
              · {benefit}
            </li>
          ))}
        </ul>
      </Card2026>

      <Card2026 className="border-dashed">
        <p className="pa26-body text-pa-muted">
          Оплата будет доступна внутри Telegram Mini App. Сейчас можно
          посмотреть возможности тарифа.
        </p>
      </Card2026>

      <Button2026 size="wide" onClick={handleOpenTelegram}>
        Открыть в Telegram
      </Button2026>

      {onRetry ? (
        <Button2026 size="wide" variant="ghost" onClick={onRetry}>
          Обновить статус
        </Button2026>
      ) : null}
    </div>
  );
}
