"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { formatAmaCost } from "@/lib/subscription/ama";

type AmaConfirmDialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  benefit?: ReactNode;
  costAma?: number | null;
  balanceAma?: number | null;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function AmaConfirmDialog({
  open,
  title,
  description,
  benefit,
  costAma,
  balanceAma,
  confirmLabel,
  cancelLabel = "Спасибо, не сейчас",
  busy = false,
  onConfirm,
  onCancel,
}: AmaConfirmDialogProps) {
  const router = useRouter();
  if (!open) return null;

  const knownCost = typeof costAma === "number" && costAma > 0;
  const unknownCost = costAma === null;
  const balanceKnown = typeof balanceAma === "number";
  const insufficient =
    knownCost && balanceKnown && (balanceAma as number) < costAma;

  const defaultConfirm = knownCost
    ? `Подтвердить · ${formatAmaCost(costAma)}`
    : "Подтвердить";

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/50 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-card bg-cream-surface p-5 shadow-lift">
        <h3 className="text-lg font-bold text-graphite-900">{title}</h3>

        <div className="mt-2 text-sm leading-relaxed text-graphite-500">
          {description}
        </div>

        {knownCost || unknownCost ? (
          <dl className="mt-4 space-y-1.5 rounded-control bg-cream-deep p-3 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-graphite-500">Стоимость</dt>
              <dd className="font-semibold text-graphite-900">
                {unknownCost
                  ? "может потребовать Амы"
                  : formatAmaCost(costAma as number)}
              </dd>
            </div>
            {balanceKnown ? (
              <div className="flex items-center justify-between">
                <dt className="text-graphite-500">Ваш баланс</dt>
                <dd className="font-semibold text-graphite-900">
                  {formatAmaCost(balanceAma as number)}
                </dd>
              </div>
            ) : null}
            {benefit ? (
              <p className="pt-1 text-xs text-graphite-500">
                Зачем это: {benefit}
              </p>
            ) : null}
          </dl>
        ) : null}

        {insufficient ? (
          <div className="mt-3 rounded-control border border-warm/30 bg-warm/10 px-3 py-2.5 text-sm text-graphite-900">
            <p>
              Сейчас Амов чуть меньше, чем нужно для этого действия. Можно
              вернуться к нему позже или посмотреть тариф.
            </p>
          </div>
        ) : null}

        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            disabled={busy}
            onClick={onCancel}
            className="pa-btn-ghost min-h-[44px] flex-1 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          {insufficient ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                onCancel();
                router.push("/subscription");
              }}
              className="pa-btn-primary min-h-[44px] flex-1 disabled:opacity-50"
            >
              Посмотреть тариф
            </button>
          ) : (
            <button
              type="button"
              disabled={busy}
              onClick={onConfirm}
              className="pa-btn-primary min-h-[44px] flex-1 disabled:opacity-50"
            >
              {busy ? "Минуточку…" : (confirmLabel ?? defaultConfirm)}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
