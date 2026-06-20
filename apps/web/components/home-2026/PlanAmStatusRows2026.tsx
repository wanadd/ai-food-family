"use client";

import { useRouter } from "next/navigation";

import {
  menuStatusLabel,
  pantryStatusLabel,
  shoppingStatusLabel,
} from "@/lib/home/planam-hero-2026";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";

type PlanAmStatusRows2026Props = {
  overview: MenuOverview | null;
  loading?: boolean;
};

type StatusCard = {
  emoji: string;
  label: string;
  value: string;
  href: string;
};

export function PlanAmStatusRows2026({
  overview,
  loading = false,
}: PlanAmStatusRows2026Props) {
  const router = useRouter();
  const unchecked = overview?.shopping_unchecked_count ?? 0;

  const cards: StatusCard[] = [
    {
      emoji: "🛒",
      label: "Купить",
      value: loading ? "…" : shoppingStatusLabel(unchecked),
      href: PLANAM_ROUTES.shopping,
    },
    {
      emoji: "📦",
      label: "Запасы",
      value: loading ? "…" : pantryStatusLabel(overview),
      href: PLANAM_ROUTES.pantry,
    },
    {
      emoji: "🍽",
      label: "Меню",
      value: loading ? "…" : menuStatusLabel(overview),
      href: PLANAM_ROUTES.planToday,
    },
  ];

  return (
    <section className="px-4 pt-2" aria-label="Статусы дня">
      <ul className="grid grid-cols-3 gap-2">
        {cards.map((card) => (
          <li key={card.label}>
            <button
              type="button"
              onClick={() => router.push(card.href)}
              className={cn(
                "flex h-full min-h-[72px] w-full flex-col items-start justify-between",
                "rounded-card border border-pa-border bg-pa-surface p-2.5 text-left shadow-soft",
                "transition active:scale-[0.99] dark:shadow-none dark:hover:bg-pa-elevated/30",
              )}
            >
              <span className="text-base" aria-hidden>
                {card.emoji}
              </span>
              <span className="min-w-0">
                <span className="pa26-micro block font-semibold text-pa-foreground">
                  {card.label}
                </span>
                <span className="pa26-micro mt-0.5 block truncate text-pa-muted">
                  {card.value}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
