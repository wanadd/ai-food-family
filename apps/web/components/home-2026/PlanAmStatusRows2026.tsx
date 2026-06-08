"use client";

import { useRouter } from "next/navigation";

import {
  pantryStatusLabel,
  shoppingStatusLabel,
  wellnessStatusLabel,
} from "@/lib/home/planam-hero-2026";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { cn } from "@/lib/planam/cn";

type PlanAmStatusRows2026Props = {
  overview: MenuOverview | null;
  loading?: boolean;
};

type StatusRow = {
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

  const rows: StatusRow[] = [
    {
      emoji: "🛒",
      label: "Купить",
      value: loading ? "…" : shoppingStatusLabel(unchecked),
      href: "/shopping",
    },
    {
      emoji: "📦",
      label: "Запасы",
      value: loading ? "…" : pantryStatusLabel(overview),
      href: "/home/pantry",
    },
    {
      emoji: "❤️",
      label: "Здоровье",
      value: loading ? "…" : wellnessStatusLabel(overview),
      href: "/wellness",
    },
  ];

  return (
    <section className="px-4 pt-2" aria-label="Статусы семьи">
      <ul className="flex flex-col gap-1.5">
        {rows.map((row) => (
          <li key={row.label}>
            <button
              type="button"
              onClick={() => router.push(row.href)}
              className={cn(
                "flex w-full min-h-10 items-center gap-3 rounded-card border border-pa-border",
                "bg-pa-surface px-3 py-2.5 text-left shadow-soft transition active:scale-[0.99]",
                "dark:shadow-none dark:hover:bg-pa-elevated/30",
              )}
            >
              <span className="text-lg" aria-hidden>
                {row.emoji}
              </span>
              <span className="min-w-0 flex-1">
                <span className="pa26-card-title block">{row.label}</span>
                <span className="pa26-micro text-pa-muted">{row.value}</span>
              </span>
              <span className="pa26-micro shrink-0 text-pa-muted" aria-hidden>
                ›
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
