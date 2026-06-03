"use client";

import Image from "next/image";
import type { ReactNode } from "react";

import { cn } from "@/lib/planam/cn";

export type ActionCard2026Props = {
  title: string;
  caption?: string;
  icon?: ReactNode;
  thumbUrl?: string | null;
  onClick?: () => void;
  className?: string;
};

function Chevron() {
  return (
    <svg
      aria-hidden
      className="size-5 shrink-0 text-pa-muted"
      viewBox="0 0 20 20"
      fill="none"
    >
      <path
        d="M7.5 5l5 5-5 5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ActionCard2026({
  title,
  caption,
  icon,
  thumbUrl,
  onClick,
  className,
}: ActionCard2026Props) {
  const leading = thumbUrl ? (
    <div className="relative size-12 shrink-0 overflow-hidden rounded-[16px] bg-cream-deep">
      <Image src={thumbUrl} alt="" fill className="object-cover" sizes="48px" unoptimized />
    </div>
  ) : icon ? (
    <div className="flex size-12 shrink-0 items-center justify-center rounded-[16px] bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
      {icon}
    </div>
  ) : null;

  const body = (
    <>
      {leading}
      <div className="min-w-0 flex-1">
        <p className="pa26-card-title truncate">{title}</p>
        {caption ? <p className="pa26-caption truncate">{caption}</p> : null}
      </div>
      <Chevron />
    </>
  );

  const shell = cn(
    "flex min-h-[64px] w-full items-center gap-3 rounded-card border border-pa-border bg-pa-surface px-4 py-3 shadow-soft transition dark:shadow-none",
    onClick && "cursor-pointer hover:bg-sage-50 active:bg-sage-50 dark:hover:bg-white/5 dark:active:bg-white/5",
    className,
  );

  if (onClick) {
    return (
      <button type="button" className={cn(shell, "text-left")} onClick={onClick}>
        {body}
      </button>
    );
  }

  return <div className={shell}>{body}</div>;
}
