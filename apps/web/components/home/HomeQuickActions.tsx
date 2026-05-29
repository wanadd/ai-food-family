"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import type { AppMode } from "@/lib/app-mode/types";
import {
  runMenuQuickAction,
  type QuickActionId,
} from "@/lib/menu/overview-api";
import { QUICK_ACTIONS, type QuickActionMeta } from "@/lib/menu/quick-actions";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);

type HomeQuickActionsProps = {
  initData: string;
  mode: AppMode;
  /** Re-fetch Home data after the active plan/shopping changed. */
  onApplied?: () => void;
};

// На Home показываем компактный набор (без «Заменить блюдо», которое требует
// выбора блюда в плане — оно остаётся в разделе «Меню»).
const HOME_ACTIONS: QuickActionMeta[] = QUICK_ACTIONS.filter(
  (action) => action.id !== "replace_dish",
);

/**
 * Блок «Быстрые действия» — те же действия над активным меню, что и в разделе
 * «Меню» (общий источник lib/menu/quick-actions). Списание Амы подтверждается
 * диалогом; после применения инвалидируем кэш и просим Home обновиться.
 */
export function HomeQuickActions({
  initData,
  mode,
  onApplied,
}: HomeQuickActionsProps) {
  const router = useRouter();
  const {
    overview: subscription,
    ensureLoaded,
    refresh: refreshSubscription,
  } = useSubscriptionOverview();
  const [acting, setActing] = useState<QuickActionId | null>(null);
  const [pendingAction, setPendingAction] = useState<QuickActionMeta | null>(
    null,
  );
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    ensureLoaded();
  }, [ensureLoaded]);

  const amaBalance = subscription?.ama_balance ?? null;
  const amaCosts = subscription?.ama_costs ?? null;

  async function runConfirmed(action: QuickActionId) {
    setActing(action);
    setMessage(null);
    try {
      const result = await runMenuQuickAction(initData, mode, action);
      if (result.redirect_path) {
        router.push(result.redirect_path);
        return;
      }
      if (result.message) setMessage(result.message);
      invalidateCache("menu-overview");
      invalidateCache("selected-menu");
      invalidateCache("shopping-list");
      invalidateCache("pantry");
      onApplied?.();
      void refreshSubscription();
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Не получилось выполнить действие. Попробуйте ещё раз.",
      );
    } finally {
      setActing(null);
      setPendingAction(null);
    }
  }

  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <p className="text-sm font-bold text-stone-900">Быстрые действия</p>
      <p className="mt-1 text-xs text-stone-500">
        Это предложения, а не требования — выбор за вами. Меню и покупки
        подстроятся под выбранную опцию.
      </p>

      {message ? (
        <p className="mt-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {message}
        </p>
      ) : null}

      <div className="mt-3 grid grid-cols-2 gap-2">
        {HOME_ACTIONS.map((action) => (
          <button
            key={action.id}
            type="button"
            disabled={Boolean(acting)}
            onClick={() => setPendingAction(action)}
            className="min-h-[44px] rounded-xl border border-stone-200 bg-stone-50 px-2 py-2.5 text-xs font-semibold text-stone-800 disabled:opacity-50"
          >
            {acting === action.id ? "…" : action.label}
          </button>
        ))}
      </div>

      <AmaConfirmDialog
        open={pendingAction !== null}
        title={pendingAction?.label ?? ""}
        description={pendingAction?.description ?? ""}
        benefit={
          pendingAction
            ? "Меню и список покупок подстроятся под выбранную опцию"
            : undefined
        }
        costAma={
          pendingAction?.costKey != null
            ? (amaCosts?.[pendingAction.costKey] ?? null)
            : null
        }
        balanceAma={amaBalance}
        busy={Boolean(acting)}
        cancelLabel="Передумал"
        confirmLabel="Да, применить"
        onCancel={() => {
          if (!acting) setPendingAction(null);
        }}
        onConfirm={() => {
          if (pendingAction) void runConfirmed(pendingAction.id);
        }}
      />
    </section>
  );
}
