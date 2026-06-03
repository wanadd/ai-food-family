"use client";

import { useRouter } from "next/navigation";

import { ActionCard2026 } from "@/components/planam-2026/cards/ActionCard2026";
import { resolveHomeRedirectPath } from "@/lib/home/redirect-path-2026";
import { shouldShowShoppingAction } from "@/lib/home/home-2026-data";
import type { HomeNextAction, HomeNextActionId } from "@/lib/menu/overview-types";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

const STRIP_ACTION_IDS: HomeNextActionId[] = [
  "shopping",
  "use_pantry_item",
  "meal_outcome",
  "complete_nutrition",
];

type NextActionCard2026Props = {
  action: HomeNextAction | null;
};

export function NextActionCard2026({ action }: NextActionCard2026Props) {
  const router = useRouter();

  if (
    !action ||
    !shouldShowShoppingAction(action) ||
    !STRIP_ACTION_IDS.includes(action.id)
  ) {
    return null;
  }

  const use2026 = isPlanamUi2026Enabled();

  return (
    <section className="px-4 pt-4" aria-label="Следующее действие">
      <p className="pa26-micro mb-2 font-semibold uppercase tracking-wide text-pa-muted">
        Сейчас
      </p>
      <ActionCard2026
        title={action.cta_label}
        caption={action.subtitle ?? undefined}
        icon={
          <span className="text-lg font-bold text-sage-600 dark:text-sage-300" aria-hidden>
            →
          </span>
        }
        onClick={() =>
          router.push(resolveHomeRedirectPath(action.redirect_path, use2026))
        }
      />
    </section>
  );
}
