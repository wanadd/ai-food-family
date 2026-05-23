"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { BottomBackButton } from "@/components/layout/BottomBackButton";

type SettingsScaffoldProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  showBack?: boolean;
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
  showBack = true,
}: SettingsScaffoldProps) {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-100 bg-white px-4 pb-4 pt-7 sm:px-5">
        <div className="mx-auto flex max-w-lg items-center gap-3">
          <Link
            href="/settings"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-stone-600 transition hover:bg-stone-100"
            aria-label="К настройкам"
          >
            <ChevronLeftIcon />
          </Link>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-bold text-stone-900">{title}</h1>
            {subtitle ? (
              <p className="mt-0.5 truncate text-sm text-stone-500">{subtitle}</p>
            ) : null}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-4 py-5 sm:px-5">{children}</main>

      {showBack ? <BottomBackButton className="pb-4 pt-2" /> : null}
    </div>
  );
}

type SettingsHubProps = {
  children: ReactNode;
};

export function SettingsHub({ children }: SettingsHubProps) {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-100 bg-white px-4 pb-4 pt-7 sm:px-5">
        <div className="mx-auto max-w-lg">
          <h1 className="text-2xl font-bold text-stone-900">Настройки</h1>
          <p className="mt-1 text-sm text-stone-500">Аккаунт и приложение</p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-5 sm:px-5">{children}</main>

      <BottomBackButton className="pb-4 pt-2" />
    </div>
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
