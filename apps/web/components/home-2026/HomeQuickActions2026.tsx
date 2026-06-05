"use client";

import { useRouter } from "next/navigation";

import { cn } from "@/lib/planam/cn";

type QuickAction = {
  id: string;
  label: string;
  caption: string;
  emoji: string;
  href?: string;
  onClick?: () => void;
};

type HomeQuickActions2026Props = {
  onLeftovers?: () => void;
  className?: string;
};

export function HomeQuickActions2026({
  onLeftovers,
  className,
}: HomeQuickActions2026Props) {
  const router = useRouter();

  const actions: QuickAction[] = [
    {
      id: "menu",
      label: "Меню",
      caption: "План на сегодня",
      emoji: "🍽",
      href: "/plan/today",
    },
    {
      id: "shopping",
      label: "Покупки",
      caption: "Список к покупке",
      emoji: "🛒",
      href: "/home/shopping",
    },
    {
      id: "leftovers",
      label: "Остатки",
      caption: "Что есть дома",
      emoji: "🍲",
      onClick: onLeftovers,
    },
    {
      id: "wellness",
      label: "Здоровье",
      caption: "Калории и цели",
      emoji: "❤️",
      href: "/wellness",
    },
  ];

  return (
    <section className={cn("px-4 pt-3", className)} aria-label="Быстрые действия">
      <h2 className="pa26-caption mb-2 font-semibold text-pa-muted">Быстрые действия</h2>
      <div className="grid grid-cols-2 gap-2">
        {actions.map((action) => (
          <button
            key={action.id}
            type="button"
            onClick={() => {
              if (action.onClick) {
                action.onClick();
                return;
              }
              if (action.href) {
                router.push(action.href);
              }
            }}
            className="flex min-h-[72px] flex-col items-start rounded-card border border-pa-border bg-pa-surface px-3 py-3 text-left shadow-soft transition active:scale-[0.98] dark:shadow-none dark:hover:bg-pa-elevated/30"
          >
            <span className="text-lg" aria-hidden>
              {action.emoji}
            </span>
            <span className="pa26-card-title mt-1">{action.label}</span>
            <span className="pa26-micro text-pa-muted">{action.caption}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
