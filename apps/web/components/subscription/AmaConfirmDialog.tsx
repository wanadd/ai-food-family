"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { formatAmaCost } from "@/lib/subscription/ama";

type AmaConfirmDialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  /**
   * Approximate cost in Amas. `null` means unknown (server-decided).
   * `0` or `undefined` means free/included.
   */
  costAma?: number | null;
  /** Current Ama balance. Optional. */
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
  costAma,
  balanceAma,
  confirmLabel,
  cancelLabel = "Отмена",
  busy = false,
  onConfirm,
  onCancel,
}: AmaConfirmDialogProps) {
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
      className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
        <h3 className="text-lg font-bold text-stone-900">{title}</h3>

        <div className="mt-2 text-sm leading-relaxed text-stone-600">
          {description}
        </div>

        {knownCost || unknownCost ? (
          <dl className="mt-4 space-y-1.5 rounded-xl bg-stone-50 p-3 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-stone-500">Стоимость</dt>
              <dd className="font-semibold text-stone-900">
                {unknownCost
                  ? "может потребовать Амы"
                  : formatAmaCost(costAma as number)}
              </dd>
            </div>
            {balanceKnown ? (
              <div className="flex items-center justify-between">
                <dt className="text-stone-500">Ваш баланс</dt>
                <dd className="font-semibold text-stone-900">
                  {formatAmaCost(balanceAma as number)}
                </dd>
              </div>
            ) : null}
          </dl>
        ) : null}

        {insufficient ? (
          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900">
            <p>На балансе пока не хватает Амов для этого действия.</p>
            <Link
              href="/subscription"
              className="mt-1.5 inline-block font-semibold text-emerald-800"
            >
              Посмотреть тариф и пополнение →
            </Link>
          </div>
        ) : null}

        <div className="mt-5 flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={onCancel}
            className="min-h-[44px] flex-1 rounded-xl border border-stone-200 px-4 text-sm font-semibold text-stone-700 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            disabled={busy || insufficient}
            onClick={onConfirm}
            className="min-h-[44px] flex-1 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
          >
            {busy ? "Минуточку…" : (confirmLabel ?? defaultConfirm)}
          </button>
        </div>
      </div>
    </div>
  );
}
