"use client";

import { useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import type { FamilyMember } from "@/lib/family/types";
import {
  formatConsumptionPortion,
  MEAL_CONSUMPTION_MEMBER_PROMPT,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_DISABLED_HINT,
  MEAL_CONSUMPTION_SHEET_SUBTITLE,
  MEAL_CONSUMPTION_SHEET_TITLE,
  MEAL_CONSUMPTION_STATUS_OPTIONS,
  type ConsumptionTargetId,
  type MealConsumptionStatus,
} from "@/lib/plan/meal-consumption-sheet";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";
import { cn } from "@/lib/planam/cn";

type MealConsumptionSheetV2Props = {
  open: boolean;
  onClose: () => void;
  meals: PlanTodayMeal[];
};

type MealDraft = {
  included: boolean;
  portion: number;
  status: MealConsumptionStatus;
};

function mealKey(item: PlanTodayMeal): string {
  return `${item.meal.meal_type}-${item.mealIndex}`;
}

function buildDefaultDrafts(meals: PlanTodayMeal[]): Record<string, MealDraft> {
  const drafts: Record<string, MealDraft> = {};
  for (const item of meals) {
    drafts[mealKey(item)] = {
      included: true,
      portion: 1,
      status: "eaten",
    };
  }
  return drafts;
}

function buildMemberTargets(
  members: FamilyMember[],
  isAdmin: boolean,
): Array<{ id: ConsumptionTargetId; label: string }> {
  if (!isAdmin) {
    const self = members.find((m) => m.is_you);
    return [{ id: "self", label: self?.display_name?.trim() || "Я" }];
  }

  const targets: Array<{ id: ConsumptionTargetId; label: string }> = [];
  const self = members.find((m) => m.is_you);
  if (self) {
    targets.push({ id: "self", label: "Я" });
  }
  for (const member of members) {
    if (member.is_you) {
      continue;
    }
    targets.push({ id: member.id, label: member.display_name });
  }
  targets.push({ id: "family", label: "Вся семья" });
  return targets;
}

export function MealConsumptionSheetV2({
  open,
  onClose,
  meals,
}: MealConsumptionSheetV2Props) {
  const { mode, context } = useAppMode();
  const [targetId, setTargetId] = useState<ConsumptionTargetId>("self");
  const [drafts, setDrafts] = useState<Record<string, MealDraft>>({});

  const familyMembers = useMemo(() => {
    if (mode !== "family" || !context?.family?.members?.length) {
      return [];
    }
    return context.family.members;
  }, [mode, context]);

  const isFamilyAdmin = context?.family?.your_role === "admin";
  const memberTargets = useMemo(
    () => buildMemberTargets(familyMembers, isFamilyAdmin),
    [familyMembers, isFamilyAdmin],
  );

  useEffect(() => {
    if (!open) {
      return;
    }
    setDrafts(buildDefaultDrafts(meals));
    setTargetId(memberTargets[0]?.id ?? "self");
  }, [open, meals, memberTargets]);

  function updateDraft(key: string, patch: Partial<MealDraft>) {
    setDrafts((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }));
  }

  return (
    <V2BottomSheet open={open} title={MEAL_CONSUMPTION_SHEET_TITLE} onClose={onClose}>
      <div className="space-y-4 pb-2">
        <p className="pa26-caption -mt-1 text-pa-muted">
          {MEAL_CONSUMPTION_SHEET_SUBTITLE}
        </p>

        {memberTargets.length > 1 ? (
          <div>
            <p className="pa26-micro mb-2 font-semibold text-pa-foreground">
              {MEAL_CONSUMPTION_MEMBER_PROMPT}
            </p>
            <div className="flex flex-wrap gap-2">
              {memberTargets.map((target) => (
                <V2Chip
                  key={String(target.id)}
                  label={target.label}
                  active={targetId === target.id}
                  onClick={() => setTargetId(target.id)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {meals.length === 0 ? (
          <p className="pa26-body text-pa-muted">На этот день блюд в плане нет.</p>
        ) : (
          <ul className="space-y-3">
            {meals.map((item) => {
              const key = mealKey(item);
              const draft = drafts[key] ?? {
                included: true,
                portion: 1,
                status: "eaten" as const,
              };
              const heading = menuMealHeading(item.meal);
              const type = mealTypeLabel(item.meal.meal_type);
              return (
                <li
                  key={key}
                  className={cn(
                    "rounded-card border border-pa-border bg-pa-surface p-3",
                    !draft.included && "opacity-60",
                  )}
                >
                  <label className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={draft.included}
                      onChange={(e) =>
                        updateDraft(key, { included: e.target.checked })
                      }
                      className="mt-1 size-4 rounded border-pa-border"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="pa26-micro text-pa-muted">{type}</span>
                      <span className="block pa26-card-title leading-snug">
                        {heading}
                      </span>
                    </span>
                  </label>
                  {draft.included ? (
                    <div className="mt-3 space-y-2 pl-6">
                      <div>
                        <p className="pa26-micro mb-1 text-pa-muted">Порция</p>
                        <div className="flex flex-wrap gap-2">
                          {MEAL_CONSUMPTION_PORTION_OPTIONS.map((portion) => (
                            <V2Chip
                              key={portion}
                              label={formatConsumptionPortion(portion)}
                              active={draft.portion === portion}
                              onClick={() => updateDraft(key, { portion })}
                            />
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="pa26-micro mb-1 text-pa-muted">Статус</p>
                        <div className="flex flex-wrap gap-2">
                          {MEAL_CONSUMPTION_STATUS_OPTIONS.map((option) => (
                            <V2Chip
                              key={option.id}
                              label={option.label}
                              active={draft.status === option.id}
                              onClick={() => updateDraft(key, { status: option.id })}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}

        <p className="pa26-micro text-pa-muted">{MEAL_CONSUMPTION_SAVE_DISABLED_HINT}</p>
        <V2Button variant="primary" className="w-full" disabled>
          Сохранить отметки
        </V2Button>
      </div>
    </V2BottomSheet>
  );
}
