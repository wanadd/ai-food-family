"use client";

import { useRouter } from "next/navigation";

import type { HomeMonetizationBanner } from "@/lib/monetization/billing-status";
import { cn } from "@/lib/planam/cn";

type HomeMonetizationBanner2026Props = {
  banner: HomeMonetizationBanner | null;
  loading?: boolean;
};

export function HomeMonetizationBanner2026({
  banner,
  loading = false,
}: HomeMonetizationBanner2026Props) {
  const router = useRouter();

  if (loading || !banner) {
    return null;
  }

  return (
    <section className="px-4 pt-3">
      <button
        type="button"
        onClick={() => router.push(banner.href)}
        className={cn(
          "w-full rounded-card border px-4 py-3 text-left transition active:scale-[0.99]",
          banner.tone === "soft"
            ? "border-sage-200 bg-sage-50/80 dark:border-sage-700/40 dark:bg-sage-700/15"
            : "border-pa-border bg-pa-surface shadow-soft dark:shadow-none",
        )}
      >
        <p className="pa26-card-title">{banner.title}</p>
        <p className="pa26-caption mt-0.5 line-clamp-2 text-pa-muted">
          {banner.description}
        </p>
        <span className="mt-2 inline-block pa26-micro font-semibold text-sage-700 dark:text-sage-300">
          {banner.ctaLabel} →
        </span>
      </button>
    </section>
  );
}
