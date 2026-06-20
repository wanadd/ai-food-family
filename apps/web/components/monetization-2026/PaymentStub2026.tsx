"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import {
  catalogEntryForCode,
  isRetailPlanCode,
  planDisplayName,
} from "@/lib/monetization/plan-catalog-2026";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";
import { selectPlanStub } from "@/lib/subscription/api";

export function PaymentStub2026() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planCode = searchParams.get("plan") ?? "";
  const returnTo = searchParams.get("returnTo");
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const { overview, patchOverview } = useSubscriptionOverview();
  const [busy, setBusy] = useState(false);

  const catalog = useMemo(
    () => (isRetailPlanCode(planCode) ? catalogEntryForCode(planCode) : null),
    [planCode],
  );

  const apiPlan = overview?.plans.find((p) => p.code === planCode);

  if (!catalog || !apiPlan) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          title="Тариф не найден"
          description="Вернитесь к выбору тарифа и попробуйте снова."
          actionLabel="К тарифам"
          onAction={() => router.push(MONETIZATION_PATHS.subscription)}
        />
      </div>
    );
  }

  async function handleStubPay() {
    if (!initData) {
      return;
    }
    setBusy(true);
    try {
      const updated = await selectPlanStub(initData, mode, planCode);
      patchOverview(updated);
      await showToast("✓ Тариф сохранён (тест без оплаты)");
      if (returnTo) {
        router.push(returnTo);
      } else {
        router.push(MONETIZATION_PATHS.subscription);
      }
    } catch (err) {
      await showToast(
        err instanceof Error ? err.message : "Не удалось сохранить тариф",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4 px-4 py-6">
      <Card2026>
        <p className="pa26-micro text-pa-muted">Оплата</p>
        <h1 className="pa26-page-title mt-1">
          {planDisplayName(planCode, apiPlan.name)}
        </h1>
        <p className="pa26-card-title mt-2 tabular-nums">
          {apiPlan.price_rub > 0 ? `${apiPlan.price_rub} ₽/мес` : "Бесплатно"}
        </p>
        <p className="pa26-body mt-3 text-pa-muted">
          Реальная оплата подключается позже. Сейчас можно сохранить тариф для
          теста — без списания с карты.
        </p>
      </Card2026>

      <ul className="space-y-1 px-1">
        {catalog.benefits.slice(0, 4).map((b) => (
          <li key={b} className="pa26-caption text-pa-muted">
            ✓ {b}
          </li>
        ))}
      </ul>

      <Button2026 size="wide" loading={busy} onClick={() => void handleStubPay()}>
        Подключить (заглушка)
      </Button2026>
      <Link
        href={MONETIZATION_PATHS.subscription}
        className="block text-center pa26-micro font-semibold text-sage-700 dark:text-sage-300"
      >
        ← Назад к тарифам
      </Link>
    </div>
  );
}
