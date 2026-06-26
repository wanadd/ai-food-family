"use client";

import type { WellnessMealSlot } from "@/lib/wellness/wellness-meals";
import { V2Card } from "@/components/planam-v2/ui/V2Primitives";
import { cn } from "@/lib/planam/cn";

type WellnessMealsSectionProps = {
  slots: WellnessMealSlot[];
  onAction: (
    slot: WellnessMealSlot,
    action: "ate_plan" | "ate_other" | "skipped" | "later",
  ) => void;
};

const STATUS_STYLES: Record<string, string> = {
  eaten: "text-sage-700 dark:text-sage-300",
  skipped: "text-orange-700 dark:text-orange-300",
  later: "text-pa-muted",
  other: "text-orange-700 dark:text-orange-300",
  planned: "text-pa-muted",
  none: "text-pa-muted",
};

export function WellnessMealsSection({
  slots,
  onAction,
}: WellnessMealsSectionProps) {
  if (slots.length === 0) {
    return null;
  }

  return (
    <section data-testid="wellness-meals-section">
      <h2 className="pa26-section-title">Приёмы пищи</h2>
      <div className="mt-2 space-y-2">
        {slots.map((slot) => (
          <V2Card key={slot.mealType} className="!p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="pa26-card-title">{slot.label}</p>
                {slot.plannedName ? (
                  <p className="pa26-micro mt-0.5 line-clamp-2 text-pa-muted">
                    {slot.plannedName}
                  </p>
                ) : (
                  <p className="pa26-micro mt-0.5 text-pa-muted">Не в меню</p>
                )}
              </div>
              <span
                className={cn(
                  "shrink-0 pa26-micro font-semibold",
                  STATUS_STYLES[slot.status] ?? STATUS_STYLES.none,
                )}
              >
                {slot.statusLabel}
              </span>
            </div>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              <MealActionChip
                label="Съел по плану"
                onClick={() => onAction(slot, "ate_plan")}
              />
              <MealActionChip
                label="Ел другое"
                onClick={() => onAction(slot, "ate_other")}
              />
              <MealActionChip
                label="Пропустил"
                onClick={() => onAction(slot, "skipped")}
              />
              <MealActionChip
                label="Съем позже"
                onClick={() => onAction(slot, "later")}
              />
            </div>
          </V2Card>
        ))}
      </div>
    </section>
  );
}

function MealActionChip({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="min-h-[36px] rounded-pill border border-pa-border bg-pa-surface px-3 py-1.5 pa26-micro font-semibold text-pa-foreground transition active:scale-[0.98]"
    >
      {label}
    </button>
  );
}
