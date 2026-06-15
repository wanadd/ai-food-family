"use client";

import { V2Chip } from "@/components/planam-v2/ui/V2Primitives";
import {
  formatPreparedLeftoverAmount,
  type CookingBatch,
} from "@/lib/plan/leftovers-api";
import type { LeftoversDraft } from "@/lib/plan/meal-leftovers-unified";
import { previewLeftoversDisplayRemaining } from "@/lib/plan/meal-leftovers-unified";

const REMAINING_PRESETS = [1, 2, 3] as const;

type PreparedLeftoversInlineV2Props = {
  batch: CookingBatch | null;
  draft: LeftoversDraft;
  canManage: boolean;
  disabled?: boolean;
  onChange: (patch: Partial<LeftoversDraft>) => void;
};

export function PreparedLeftoversInlineV2({
  batch,
  draft,
  canManage,
  disabled = false,
  onChange,
}: PreparedLeftoversInlineV2Props) {
  const displayRemaining = previewLeftoversDisplayRemaining(draft, batch);
  const displayTotal = batch?.total_servings ?? draft.totalServings;

  function markTouched(patch: Partial<LeftoversDraft>) {
    onChange({ ...patch, touched: true });
  }

  return (
    <div className="mt-3 space-y-2 rounded-card border border-dashed border-pa-border bg-pa-bg/50 p-3 pl-8">
      <p className="pa26-micro font-semibold text-pa-foreground">
        Готовая еда и остатки
      </p>

      {!canManage ? (
        <p className="pa26-micro text-pa-muted">
          Только админ семьи может менять общие остатки
        </p>
      ) : null}

      <div>
        <p className="pa26-micro mb-1 text-pa-muted">Приготовлено</p>
        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={!canManage || disabled || Boolean(batch)}
            className="flex size-8 items-center justify-center rounded-full border border-pa-border text-lg"
            onClick={() =>
              markTouched({
                totalServings: Math.max(1, draft.totalServings - 1),
              })
            }
          >
            −
          </button>
          <span className="pa26-body min-w-[4rem] text-center">
            {draft.totalServings}{" "}
            {draft.servingUnit === "порция" ? "порций" : draft.servingUnit}
          </span>
          <button
            type="button"
            disabled={!canManage || disabled || Boolean(batch)}
            className="flex size-8 items-center justify-center rounded-full border border-pa-border text-lg"
            onClick={() =>
              markTouched({ totalServings: draft.totalServings + 1 })
            }
          >
            +
          </button>
        </div>
      </div>

      {draft.yieldType !== "servings" ? (
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            inputMode="decimal"
            disabled={!canManage || disabled || Boolean(batch)}
            value={draft.totalAmountValue ?? ""}
            placeholder="Приготовлено"
            onChange={(e) =>
              markTouched({
                totalAmountValue: Number(e.target.value.replace(",", ".")) || null,
                totalAmountUnit: draft.totalAmountUnit ?? "л",
              })
            }
            className="rounded-control border border-pa-border bg-pa-surface px-3 py-2 pa26-body"
          />
          <input
            type="text"
            inputMode="decimal"
            disabled={!canManage || disabled}
            value={draft.remainingAmountValue ?? ""}
            placeholder="Осталось"
            onChange={(e) =>
              markTouched({
                remainingAmountValue:
                  Number(e.target.value.replace(",", ".")) || null,
                remainingAmountUnit: draft.remainingAmountUnit ?? "л",
              })
            }
            className="rounded-control border border-pa-border bg-pa-surface px-3 py-2 pa26-body"
          />
        </div>
      ) : null}

      <div>
        <p className="pa26-micro mb-1 text-pa-muted">Осталось</p>
        <p className="pa26-caption font-medium">
          {formatPreparedLeftoverAmount(
            displayRemaining,
            displayTotal,
            draft.servingUnit,
            {
              remaining_amount_value:
                draft.remainingAmountValue ?? batch?.remaining_amount_value,
              remaining_amount_unit:
                draft.remainingAmountUnit ?? batch?.remaining_amount_unit,
              total_amount_value:
                draft.totalAmountValue ?? batch?.total_amount_value,
              total_amount_unit:
                draft.totalAmountUnit ?? batch?.total_amount_unit,
            },
          )}
        </p>
      </div>

      {canManage ? (
        <div className="flex flex-wrap gap-2">
          <V2Chip
            label="Всё съели"
            active={draft.quickAction === "finish"}
            disabled={disabled}
            onClick={() =>
              markTouched({
                quickAction: "finish",
                remainingTarget: null,
                customRemaining: "",
              })
            }
          />
          {REMAINING_PRESETS.map((n) => (
            <V2Chip
              key={n}
              label={`Осталось ${n}`}
              active={
                draft.quickAction == null &&
                draft.remainingTarget === n &&
                !draft.customRemaining
              }
              disabled={disabled}
              onClick={() =>
                markTouched({
                  quickAction: null,
                  remainingTarget: n,
                  customRemaining: "",
                })
              }
            />
          ))}
          <V2Chip
            label="Другое"
            active={
              draft.quickAction == null &&
              draft.remainingTarget == null &&
              draft.customRemaining !== ""
            }
            disabled={disabled}
            onClick={() =>
              markTouched({
                quickAction: null,
                remainingTarget: null,
              })
            }
          />
          <V2Chip
            label="Выбросили"
            active={draft.quickAction === "discard"}
            disabled={disabled}
            onClick={() =>
              markTouched({
                quickAction: "discard",
                remainingTarget: null,
                customRemaining: "",
              })
            }
          />
        </div>
      ) : null}

      {canManage &&
      draft.quickAction == null &&
      draft.remainingTarget == null ? (
        <input
          type="text"
          inputMode="decimal"
          value={draft.customRemaining}
          disabled={disabled}
          onChange={(e) =>
            markTouched({
              customRemaining: e.target.value,
              remainingTarget: null,
              quickAction: null,
            })
          }
          placeholder="Сколько осталось?"
          className="w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2 pa26-body"
        />
      ) : null}
    </div>
  );
}
