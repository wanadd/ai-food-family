"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";

type SettingsScaffoldProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

function ChevronLeftIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
      <path
        d="M15 18l-6-6 6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SettingsScaffold({
  title,
  subtitle,
  children,
}: SettingsScaffoldProps) {
  return (
    <ScreenLayout
      title={title}
      subtitle={subtitle}
      back={{ label: "Настройки", href: "/settings" }}
    >
      {children}
    </ScreenLayout>
  );
}

type SettingsHubProps = {
  children: ReactNode;
};

export function SettingsHub({ children }: SettingsHubProps) {
  return (
    <ScreenLayout
      title="Настройки"
      subtitle="Аккаунт и приложение"
      back={{ label: "Профиль", href: "/profile" }}
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
  const className =
    "flex min-h-[56px] items-center gap-3 rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm transition active:scale-[0.99] hover:border-emerald-200";

  const content = (
    <>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-stone-900">{label}</p>
        {description ? (
          <p className="mt-0.5 text-sm text-stone-500">{description}</p>
        ) : null}
      </div>
      <span className="shrink-0 text-stone-400" aria-hidden>
        ›
      </span>
    </>
  );

  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {content}
      </a>
    );
  }

  return (
    <Link href={href} className={className}>
      {content}
    </Link>
  );
}
