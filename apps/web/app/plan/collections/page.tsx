"use client";

import { useRouter } from "next/navigation";

import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { PLANAM_ROUTES } from "@/lib/planam/routes";

export default function PlanCollectionsPage() {
  const router = useRouter();

  return (
    <div className="px-4 py-8">
      <EmptyState2026
        icon={<span aria-hidden>📚</span>}
        title="Коллекции рецептов"
        description="Подборки блюд появятся здесь — пока можно искать в общем каталоге."
        actionLabel="Открыть рецепты"
        onAction={() => router.push(PLANAM_ROUTES.recipes)}
      />
    </div>
  );
}
