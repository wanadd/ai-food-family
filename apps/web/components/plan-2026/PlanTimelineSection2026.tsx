import { PlanMealCard2026 } from "@/components/plan-2026/PlanMealCard2026";
import type { PlanTodayTimelineGroup } from "@/lib/plan/plan-today";

type PlanTimelineSection2026Props = {
  groups: PlanTodayTimelineGroup[];
  onCook: (mealIndex: number) => void;
  onReplace: (slotId: string, currentRecipeId: number | null) => void;
  onRemove?: (slotId: string) => void;
};

export function PlanTimelineSection2026({
  groups,
  onCook,
  onReplace,
  onRemove,
}: PlanTimelineSection2026Props) {
  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <section key={group.slot.id}>
          <h2 className="pa26-section-title flex items-center gap-2">
            <span aria-hidden>{group.slot.emoji}</span>
            {group.slot.label}
          </h2>
          <div className="mt-3 space-y-3">
            {group.meals.map((item) => (
              <PlanMealCard2026
                key={`${item.meal.meal_type}-${item.mealIndex}`}
                item={item}
                onCook={() => onCook(item.mealIndex)}
                onReplace={() =>
                  onReplace(item.slotId ?? "", item.meal.recipe_id ?? null)
                }
                onRemove={
                  item.slotId && onRemove
                    ? () => onRemove(item.slotId!)
                    : undefined
                }
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
