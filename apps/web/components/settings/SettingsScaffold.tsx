"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { usePlanam2026Embedded } from "@/lib/planam/embedded-2026";

type SettingsScaffoldProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

function SettingsFrame({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pb-6 pt-[max(0.75rem,env(safe-area-inset-top))]">
      {children}
    </div>
  );
}

export function SettingsScaffold({
  title,
  subtitle,
  children,
}: SettingsScaffoldProps) {
  const embedded = usePlanam2026Embedded("/account/settings");

  if (embedded) {
    return <SettingsFrame>{children}</SettingsFrame>;
  }

  return (
    <ScreenLayout
      title={title}
      subtitle={subtitle}
      back={{ label: "Настройки", href: "/account/settings" }}
    >
      {children}
    </ScreenLayout>
  );
}

type SettingsHubProps = {
  children: ReactNode;
};

export function SettingsHub({ children }: SettingsHubProps) {
  const embedded = usePlanam2026Embedded("/account/settings");

  if (embedded) {
    return <SettingsFrame>{children}</SettingsFrame>;
  }

  return (
    <ScreenLayout
      title="Настройки"
      subtitle="Аккаунт и приложение"
      back={{ label: "Профиль", href: "/account" }}
      contentClassName="space-y-3"
    >
      {children}
    </ScreenLayout>
  );
}

type SettingsMenuItemProps = {
  href: string;
  label: string;
  description?: string;
  external?: boolean;
};

export function SettingsMenuItem({
  href,
  label,
  description,
  external,
}: SettingsMenuItemProps) {
  const pathname = usePathname();
  const resolvedHref =
    pathname.startsWith("/account/settings") && href.startsWith("/settings")
      ? href.replace("/settings", "/account/settings")
      : href;

  const className =
    "flex min-h-[58px] items-center gap-3 rounded-card border border-pa-border bg-pa-surface px-4 py-3 shadow-soft transition active:scale-[0.99] hover:bg-sage-50 dark:shadow-none dark:hover:bg-pa-elevated/40";

  const content = (
    <>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-pa-foreground">{label}</p>
        {description ? (
          <p className="mt-0.5 text-xs text-pa-muted">{description}</p>
        ) : null}
      </div>
      <span className="shrink-0 text-pa-muted" aria-hidden>
        ›
      </span>
    </>
  );

  if (external) {
    return (
      <a
        href={resolvedHref}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
      >
        {content}
      </a>
    );
  }

  return (
    <Link href={resolvedHref} className={className}>
      {content}
    </Link>
  );
}
