"use client";

import Link from "next/link";

import { ActionCard2026 } from "@/components/planam-2026/cards/ActionCard2026";
import { NavIcon2026 } from "@/components/planam-2026/navigation/NavIcon2026";
import { ThemeToggle2026 } from "@/components/planam-2026/theme/ThemeToggle2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { ACCOUNT_HUB_ITEMS_2026 } from "@/lib/navigation/nav-config-2026";

export function AccountHub2026() {
  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 py-6">
      <Card2026>
        <p className="pa26-body text-pa-muted">
          Профиль, подписка и настройки — в одном месте.
        </p>
      </Card2026>

      <div className="space-y-2">
        {ACCOUNT_HUB_ITEMS_2026.map((item) => {
          if (item.inline === "theme") {
            return (
              <Card2026 key={item.id}>
                <div className="flex items-start gap-3">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-[16px] bg-sage-50 dark:bg-sage-700/30">
                    <NavIcon2026 id={item.icon} className="text-sage-700 dark:text-sage-300" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="pa26-card-title">{item.label}</p>
                    {item.caption ? (
                      <p className="pa26-caption">{item.caption}</p>
                    ) : null}
                    <div className="mt-3">
                      <ThemeToggle2026 />
                    </div>
                  </div>
                </div>
              </Card2026>
            );
          }

          return (
            <Link key={item.id} href={item.href} className="block">
              <ActionCard2026
                title={item.label}
                caption={item.caption}
                icon={
                  <NavIcon2026
                    id={item.icon}
                    className="text-sage-700 dark:text-sage-300"
                  />
                }
              />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
