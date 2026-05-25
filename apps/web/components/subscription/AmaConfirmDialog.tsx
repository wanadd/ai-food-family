"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { formatAmaCost } from "@/lib/subscription/ama";

type AmaConfirmDialogProps = {
  open: boolean;
  title: string;
  /** What the action will do, in user-friendly language. */
  description: ReactNode;
  /**
   * Short, optional positive framing: what the user gets out of
   * spending the Amas. Shown as a calm "Зачем это" hint inside the
   * cost panel. Examples:
   *   "Поможет подобрать блюдо точнее под семью"
   *   "Ама-нутрициолог разберёт ситуацию и предложит шаги"
   */
  benefit?: ReactNode;
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
            {benefit ? (
              <p className="pt-1 text-xs text-stone-500">
                Зачем это: {benefit}
              </p>
            ) : null}
          </dl>
        ) : null}

        {insufficient ? (
          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900">
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
            className="min-h-[44px] flex-1 rounded-xl border border-stone-200 px-4 text-sm font-semibold text-stone-700 disabled:opacity-50"
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
              className="min-h-[44px] flex-1 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
            >
              Посмотреть тариф
            </button>
          ) : (
            <button
              type="button"
              disabled={busy}
              onClick={onConfirm}
              className="min-h-[44px] flex-1 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
            >
              {busy ? "Минуточку…" : (confirmLabel ?? defaultConfirm)}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
