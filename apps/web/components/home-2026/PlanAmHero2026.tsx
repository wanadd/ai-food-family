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

function HeroVisual({
  state,
  compact,
}: {
  state: PlanAmHeroState;
  compact: boolean;
}) {
  const heightClass = compact ? "h-32" : "aspect-video min-h-[128px]";

  if (state.variant === "meal" && state.meal) {
    return (
      <div className={cn("relative w-full overflow-hidden", heightClass)}>
        {state.meal.image_url ? (
          <Image
            src={state.meal.image_url}
            alt={state.meal.name}
            fill
            className="object-cover"
            sizes="100vw"
            unoptimized
            priority
          />
        ) : (
          <MealFallbackPlate2026 mealType={state.meal.meal_type} />
        )}
      </div>
    );
  }

  if (state.variant === "shopping") {
    return (
      <div
        className={cn(
          "flex w-full flex-col items-center justify-center gap-2 bg-cream-deep dark:bg-graphite-700/40",
          heightClass,
        )}
      >
        <span className="text-5xl" aria-hidden>
          🛒
        </span>
        <span className="pa26-caption text-pa-muted">Список покупок</span>
      </div>
    );
  }

  if (state.variant === "wellness") {
    return (
      <div
        className={cn(
          "flex w-full flex-col items-center justify-center gap-2 bg-cream-deep dark:bg-graphite-700/40",
          heightClass,
        )}
      >
        <span className="text-5xl" aria-hidden>
          ❤️
        </span>
        <span className="pa26-caption text-pa-muted">Здоровье</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex w-full flex-col items-center justify-center gap-2 bg-cream-deep dark:bg-graphite-700/40",
        heightClass,
      )}
    >
      <span className="text-5xl" aria-hidden>
        ✨
      </span>
      <span className="pa26-caption text-pa-muted">Меню на неделю</span>
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
          className={cn("rounded-card w-full", compact ? "h-32" : "aspect-video")}
        />
        <Skeleton2026 variant="text" className="mt-4 max-w-[200px]" />
        <Skeleton2026 variant="rect" className="mt-3 h-11 w-full rounded-control" />
      </section>
    );
  }

  return (
    <section className="px-4 pt-2" aria-label="Главное действие">
      <div className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none">
        <HeroVisual state={state} compact={compact} />
        <div className="p-4">
          <h2 className="pa26-hero line-clamp-2">{state.title}</h2>
          <p className="pa26-caption mt-1 line-clamp-2 text-pa-muted">{state.subtitle}</p>
          <Button2026
            variant="primary"
            size="wide"
            className="mt-4"
            onClick={() => router.push(state.ctaHref)}
          >
            {state.ctaLabel}
          </Button2026>
        </div>
      </div>
    </section>
  );
}
