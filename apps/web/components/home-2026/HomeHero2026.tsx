"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { resolveHomeRedirectPath } from "@/lib/home/redirect-path-2026";
import {
  formatMealMeta,
  type Home2026TodayMeal,
} from "@/lib/home/home-2026-data";
import type { HomeNextAction } from "@/lib/menu/overview-types";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { cn } from "@/lib/planam/cn";

export type HomeHero2026Props = {
  loading?: boolean;
  hasMenu: boolean;
  heroMeal: Home2026TodayMeal | null;
  nextAction: HomeNextAction | null;
  isNewUser?: boolean;
  urgent?: boolean;
};

export function HomeHero2026({
  loading = false,
  hasMenu,
  heroMeal,
  nextAction,
  isNewUser = false,
  urgent = false,
}: HomeHero2026Props) {
  const router = useRouter();
  const use2026 = isPlanamUi2026Enabled();

  const handleCta = () => {
    if (!nextAction?.redirect_path) {
      return;
    }
    router.push(
      resolveHomeRedirectPath(nextAction.redirect_path, use2026, nextAction.id),
    );
  };

  if (loading) {
    return (
      <section className="px-4 pt-2" aria-busy="true">
        <Skeleton2026 variant="rect" aspectRatio="16/9" className="rounded-card" />
        <Skeleton2026 variant="text" className="mt-4 max-w-[200px]" />
        <Skeleton2026 variant="rect" className="mt-3 h-11 w-full rounded-control" />
      </section>
    );
  }

  const showDish = hasMenu && heroMeal && nextAction?.id !== "generate_menu";
  const ctaLabel =
    nextAction?.cta_label ??
    (hasMenu ? "Что готовим сегодня" : "Создать первое меню");

  const title = showDish
    ? heroMeal!.name
    : nextAction?.id === "generate_menu"
      ? isNewUser
        ? "Добро пожаловать в ПланАм"
        : "Создать первое меню"
      : nextAction?.cta_label ?? "Ваш день";

  const caption = showDish
    ? formatMealMeta(heroMeal!)
    : nextAction?.subtitle ??
      (isNewUser
        ? "План на неделю за пару минут — с фото блюд и списком покупок"
        : "Составьте меню — и здесь появятся блюда на сегодня");

  return (
    <section className="px-4 pt-2">
      <div
        className={cn(
          "overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none",
          urgent && "ring-1 ring-warm/40",
        )}
      >
        <div className="relative aspect-video w-full">
          {showDish ? (
            heroMeal!.image_url ? (
              <Image
                src={heroMeal!.image_url}
                alt={heroMeal!.name}
                fill
                className="object-cover"
                sizes="100vw"
                unoptimized
                priority
              />
            ) : (
              <MealFallbackPlate2026 mealType={heroMeal!.meal_type} />
            )
          ) : (
            <MealFallbackPlate2026 mealType="dinner" />
          )}
        </div>
        <div className="p-4">
          <h2 className="pa26-hero line-clamp-2">{title}</h2>
          <p className="pa26-caption mt-1 line-clamp-2">{caption}</p>
          <Button2026
            variant="primary"
            size="wide"
            className="mt-4"
            onClick={handleCta}
          >
            {ctaLabel}
          </Button2026>
        </div>
      </div>
    </section>
  );
}
