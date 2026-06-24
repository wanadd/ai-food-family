"use client";

import Link from "next/link";

import { NavIcon2026 } from "@/components/planam-2026/navigation/NavIcon2026";
import { ThemeToggle2026 } from "@/components/planam-2026/theme/ThemeToggle2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  formatAccountDisplayName,
  formatAccountUsernameLabel,
} from "@/lib/display/sanitize-label";
import type { Nav2026IconId } from "@/lib/navigation/nav-config-2026";

type AccountSurfaceLink = {
  title: string;
  caption: string;
  href: string;
  icon: Nav2026IconId;
};

const ACCOUNT_GROUPS: {
  title: string;
  caption: string;
  links: AccountSurfaceLink[];
}[] = [
  {
    title: "Семья",
    caption: "Участники, роли и приглашения",
    links: [
      {
        title: "Семья и участники",
        caption: "Профили близких для общего меню",
        href: "/account/family",
        icon: "family",
      },
    ],
  },
  {
    title: "Питание",
    caption: "Ограничения, аллергии и цели",
    links: [
      {
        title: "Профиль питания",
        caption: "Цели, бюджет, любимое и нелюбимое",
        href: "/account/nutrition",
        icon: "profile",
      },
    ],
  },
  {
    title: "Уведомления",
    caption: "Готовка, покупки, здоровье и тихие часы",
    links: [
      {
        title: "Настроить заботу",
        caption: "Мягкие напоминания в Telegram",
        href: "/account/notifications",
        icon: "notifications",
      },
    ],
  },
  {
    title: "Приложение",
    caption: "Тема, документы, поддержка и информация",
    links: [
      {
        title: "Настройки",
        caption: "Внешний вид, документы и поддержка",
        href: "/account/settings",
        icon: "settings",
      },
    ],
  },
];

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
      <div
        className="size-14 shrink-0 rounded-[18px] bg-cover bg-center ring-2 ring-pa-border"
        style={{ backgroundImage: `url(${photoUrl})` }}
        aria-hidden
      />
    );
  }
  return (
    <div
      className="flex size-14 shrink-0 items-center justify-center rounded-[18px] bg-sage-500 text-xl font-bold text-white"
      aria-hidden
    >
      {initial}
    </div>
  );
}

export function AccountHub2026() {
  const { user } = useTelegram();
  const fullName = formatAccountDisplayName(
    user?.first_name,
    user?.last_name,
    user?.username,
  );
  const usernameLabel = formatAccountUsernameLabel(user?.username);

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 py-3 pb-6 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <header className="space-y-1">
        <h1 className="pa26-page-title">Профиль</h1>
        <p className="pa26-body text-pa-muted">
          Аккаунт, семья, питание и настройки приложения.
        </p>
      </header>

      <Card2026 padding="md" className="!p-4">
        <div className="flex items-center gap-3">
          <UserAvatar name={fullName} photoUrl={user?.photo_url} />
          <div className="min-w-0 flex-1">
            <p className="pa26-card-title truncate">{user ? fullName : "Профиль PLANAM"}</p>
            <p className="pa26-caption text-pa-muted">
              {user ? usernameLabel : "Откройте Mini App в Telegram для полного профиля"}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="rounded-pill bg-sage-50 px-2.5 py-1 text-xs font-semibold text-sage-700 dark:bg-sage-700/30 dark:text-sage-200">
                Free
              </span>
              <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-pa-muted dark:bg-pa-elevated">
                Закрытое тестирование
              </span>
            </div>
          </div>
        </div>
      </Card2026>

      <Card2026 padding="md" className="!p-4">
        <div className="flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-[14px] bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
            <NavIcon2026 id="theme" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="pa26-card-title">Внешний вид</p>
            <p className="pa26-caption text-pa-muted">Светлая, тёмная или системная тема</p>
            <div className="mt-3">
              <ThemeToggle2026 />
            </div>
          </div>
        </div>
      </Card2026>

      <div className="space-y-3">
        {ACCOUNT_GROUPS.map((group) => (
          <Card2026 key={group.title} padding="md" className="!p-4">
            <div className="mb-3">
              <p className="pa26-card-title">{group.title}</p>
              <p className="pa26-caption text-pa-muted">{group.caption}</p>
            </div>
            <div className="space-y-2">
              {group.links.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex min-h-[58px] items-center gap-3 rounded-[18px] bg-cream-deep/60 px-3 py-2.5 transition hover:bg-sage-50 active:scale-[0.99] dark:bg-pa-elevated/50 dark:hover:bg-pa-elevated"
                >
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-[14px] bg-pa-surface text-sage-700 dark:bg-pa-surface dark:text-sage-300">
                    <NavIcon2026 id={item.icon} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-semibold text-pa-foreground">
                      {item.title}
                    </span>
                    <span className="block truncate text-xs text-pa-muted">
                      {item.caption}
                    </span>
                  </span>
                  <span className="text-pa-muted" aria-hidden>
                    ›
                  </span>
                </Link>
              ))}
            </div>
          </Card2026>
        ))}
      </div>
    </div>
  );
}
