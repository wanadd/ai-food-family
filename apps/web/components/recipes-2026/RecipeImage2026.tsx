"use client";

import Image from "next/image";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import {
  hasRecipeImage,
  recipeAspectClass,
  recipeImageSizes,
  resolveRecipeImageUrl,
  type RecipeImageSource,
  type RecipeMediaVariant,
} from "@/lib/recipes/recipe-media";
import { cn } from "@/lib/planam/cn";

type RecipeImage2026Props = {
  imageUrl?: string | null;
  imageSource?: RecipeImageSource | null;
  alt: string;
  variant: RecipeMediaVariant;
  mealType?: string;
  className?: string;
  priority?: boolean;
};

export function RecipeImage2026({
  imageUrl,
  imageSource,
  alt,
  variant,
  mealType = "dinner",
  className,
  priority = false,
}: RecipeImage2026Props) {
  const src = resolveRecipeImageUrl(imageSource ?? imageUrl, variant);
  const showImage = hasRecipeImage(src);

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden bg-cream-deep dark:bg-graphite-700/30",
        recipeAspectClass(variant),
        className,
      )}
    >
      {showImage && src ? (
        <Image
          src={src}
          alt={alt}
          fill
          className="object-cover"
          sizes={recipeImageSizes(variant)}
          unoptimized
          priority={priority}
        />
      ) : (
        <MealFallbackPlate2026 mealType={mealType} className="absolute inset-0" />
      )}
    </div>
  );
}
