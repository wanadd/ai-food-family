"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import type { PlanAmHeroState } from "@/lib/home/planam-hero-2026";
import { useCompactViewport } from "@/lib/home/use-compact-viewport";
import { cn } from "@/lib/planam/cn";

export type PlanAmHero2026Props = {
  loading?: boolean;
  state: PlanAmHeroState;
};

function MealHeroCard({
  state,
  compact,
  onCta,
  onSecondaryCta,
}: {
  state: PlanAmHeroState;
  compact: boolean;
  onCta: () => void;
  onSecondaryCta?: () => void;
}) {
  const meal = state.meal!;
  const heightClass = compact ? "min-h-[180px]" : "min-h-[200px]";

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-card",
        heightClass,
      )}
    >
      {meal.image_url ? (
        <Image
          src={meal.image_url}
          alt={meal.name}
          fill
          className="object-cover"
          sizes="100vw"
          unoptimized
          priority
        />
      ) : (
        <MealFallbackPlate2026 mealType={meal.meal_type} className="absolute inset-0" />
      )}
      <div
        className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/15 to-transparent"
        aria-hidden
      />
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/55 to-transparent p-3 pt-8 text-white">
        {meal.label ? (
          <p className="pa26-micro font-semibold uppercase tracking-wide text-white/80">
            {meal.label}
          </p>
        ) : null}
        <h2 className="pa26-hero mt-0.5 line-clamp-2 text-white">{state.title}</h2>
        <p className="pa26-caption mt-1 text-white/85">{state.subtitle}</p>
        <div className="mt-2 flex flex-col gap-2">
          <Button2026 variant="primary" size="wide" onClick={onCta}>
            {state.ctaLabel}
          </Button2026>
          {state.secondaryCtaLabel && onSecondaryCta ? (
            <Button2026
              variant="secondary"
              size="wide"
              className="border-white/30 bg-black/25 text-white hover:bg-black/35 dark:border-white/25 dark:bg-black/35 dark:hover:bg-black/45"
              onClick={onSecondaryCta}
            >
              {state.secondaryCtaLabel}
            </Button2026>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ContextHeroCard({
  state,
  onCta,
}: {
  state: PlanAmHeroState;
  onCta: () => void;
}) {
  const icon =
    state.variant === "shopping"
      ? "🛒"
      : state.variant === "wellness"
        ? "💚"
        : state.variant === "nutrition_profile"
          ? "🎯"
          : state.variant === "pantry_expiry"
            ? "📦"
            : state.variant === "meal_outcome"
              ? "✅"
              : "✨";

  return (
    <div className="overflow-hidden rounded-card border border-pa-border bg-pa-elevated shadow-soft dark:shadow-none">
      <div className="flex items-start gap-3 p-4">
        <span
          className="flex size-11 shrink-0 items-center justify-center rounded-[14px] bg-sage-50 text-2xl dark:bg-sage-700/30"
          aria-hidden
        >
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="pa26-card-title line-clamp-2">{state.title}</h2>
          <p className="pa26-caption mt-1 line-clamp-3 text-pa-muted">{state.subtitle}</p>
        </div>
      </div>
      <div className="border-t border-pa-border px-4 pb-4 pt-3">
        <Button2026 variant="primary" size="wide" onClick={onCta}>
          {state.ctaLabel}
        </Button2026>
      </div>
    </div>
  );
}

export function PlanAmHero2026({ loading = false, state }: PlanAmHero2026Props) {
  const router = useRouter();
  const compact = useCompactViewport();

  if (loading) {
    return (
      <section className="px-4 pt-2" aria-busy="true">
        <Skeleton2026
          variant="rect"
          className={cn("rounded-card w-full", compact ? "min-h-[180px]" : "min-h-[200px]")}
        />
      </section>
    );
  }

  const goCta = () => router.push(state.ctaHref);
  const goSecondary = state.secondaryCtaHref
    ? () => router.push(state.secondaryCtaHref!)
    : undefined;

  return (
    <section className="px-4 pt-1" aria-label="Главное действие">
      {state.variant === "meal" && state.meal ? (
        <MealHeroCard
          state={state}
          compact={compact}
          onCta={goCta}
          onSecondaryCta={goSecondary}
        />
      ) : (
        <ContextHeroCard state={state} onCta={goCta} />
      )}
    </section>
  );
}
