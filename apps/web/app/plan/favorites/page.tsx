"use client";

import { useRouter } from "next/navigation";

import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { PLANAM_ROUTES } from "@/lib/planam/routes";

export default function PlanFavoritesPage() {
  const router = useRouter();

  return (
    <div className="px-4 py-8">
      <EmptyState2026
        icon={<span aria-hidden>⭐</span>}
        title="Избранные рецепты"
        description="Сохраняйте понравившиеся блюда в каталоге — они появятся здесь."
        actionLabel="Открыть рецепты"
        onAction={() => router.push(`${PLANAM_ROUTES.recipes}?favorites_only=true`)}
      />
    </div>
  );
}
