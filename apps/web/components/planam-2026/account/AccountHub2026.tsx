"use client";

import Link from "next/link";

import { ActionCard2026 } from "@/components/planam-2026/cards/ActionCard2026";
import { NavIcon2026 } from "@/components/planam-2026/navigation/NavIcon2026";
import { ThemeToggle2026 } from "@/components/planam-2026/theme/ThemeToggle2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { useTelegram } from "@/components/TelegramProvider";
import { ACCOUNT_HUB_ITEMS_2026 } from "@/lib/navigation/nav-config-2026";

function UserAvatar({
  name,
  photoUrl,
}: {
  name: string;
  photoUrl: string | null | undefined;
}) {
  const initial = name.trim().charAt(0).toUpperCase() || "П";
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt=""
        className="size-11 shrink-0 rounded-[14px] object-cover ring-2 ring-pa-border"
      />
    );
  }
  return (
    <div
      className="flex size-11 shrink-0 items-center justify-center rounded-[14px] bg-sage-500 text-lg font-bold text-white"
      aria-hidden
    >
      {initial}
    </div>
  );
}

export function AccountHub2026() {
  const { user } = useTelegram();
  const fullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    "Пользователь";

  return (
    <div className="mx-auto max-w-lg space-y-3 px-4 py-3 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <header>
        <h1 className="pa26-page-title">Профиль</h1>
      </header>

      {user ? (
        <Card2026 padding="md" className="!p-3">
          <div className="flex items-center gap-3">
            <UserAvatar name={fullName} photoUrl={user.photo_url} />
            <div className="min-w-0 flex-1">
              <p className="pa26-card-title truncate">{fullName}</p>
              <p className="pa26-caption text-pa-muted">
                {user.username ? `@${user.username}` : "Ваш аккаунт"}
              </p>
            </div>
          </div>
        </Card2026>
      ) : (
        <Card2026 padding="md" className="!p-3">
          <p className="pa26-body text-pa-muted">
            Профиль, подписка и настройки — в одном месте.
          </p>
        </Card2026>
      )}

      <div className="space-y-1.5">
        {ACCOUNT_HUB_ITEMS_2026.map((item) => {
          if (item.inline === "theme") {
            return (
              <Card2026 key={item.id} padding="md" className="!p-3">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-[12px] bg-sage-50 dark:bg-sage-700/30">
                    <NavIcon2026 id={item.icon} className="text-sage-700 dark:text-sage-300" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="pa26-card-title">{item.label}</p>
                    <div className="mt-2">
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
                className="min-h-[52px] !px-3 !py-2.5"
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
