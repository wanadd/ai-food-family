"use client";

import Image from "next/image";
import type { ReactNode } from "react";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { cn } from "@/lib/planam/cn";

export type HeroCard2026Aspect = "4:3" | "16:9";

export type HeroCard2026Props = {
  title: string;
  caption?: string;
  imageUrl?: string | null;
  imageAlt?: string;
  aspect?: HeroCard2026Aspect;
  ctaLabel?: string;
  onCta?: () => void;
  onClick?: () => void;
  loading?: boolean;
  className?: string;
  trailing?: ReactNode;
};

const aspectClass: Record<HeroCard2026Aspect, string> = {
  "4:3": "aspect-[4/3]",
  "16:9": "aspect-video",
};

export function HeroCard2026({
  title,
  caption,
  imageUrl,
  imageAlt = "",
  aspect = "4:3",
  ctaLabel,
  onCta,
  onClick,
  loading = false,
  className,
  trailing,
}: HeroCard2026Props) {
  const interactive = Boolean(onClick);

  const content = (
    <>
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-t-card bg-cream-deep dark:bg-graphite-700/30",
          aspectClass[aspect],
        )}
      >
        {loading ? (
          <Skeleton2026 variant="rect" className="absolute inset-0 h-full rounded-none" />
        ) : imageUrl ? (
          <Image
            src={imageUrl}
            alt={imageAlt || title}
            fill
            className="object-cover"
            sizes="(max-width: 320px) 72vw, 320px"
            unoptimized
          />
        ) : (
          <div className="flex h-full items-center justify-center pa26-caption text-pa-muted">
            Блюдо
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="pa26-card-title truncate">{title}</h3>
            {caption ? <p className="pa26-caption mt-1">{caption}</p> : null}
          </div>
          {trailing}
        </div>
        {ctaLabel && onCta ? (
          <Button2026 variant="primary" size="wide" className="mt-3" onClick={onCta}>
            {ctaLabel}
          </Button2026>
        ) : null}
      </div>
    </>
  );

  const shellClass = cn(
    "w-full max-w-[320px] shrink-0 overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft transition dark:shadow-none",
    interactive && "active:scale-[0.98] cursor-pointer",
    className,
  );

  if (interactive && !ctaLabel) {
    return (
      <button type="button" className={cn(shellClass, "text-left")} onClick={onClick}>
        {content}
      </button>
    );
  }

  return <article className={shellClass}>{content}</article>;
}
