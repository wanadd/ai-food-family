import { Suspense } from "react";

import { MenuSectionLayout } from "@/components/menu/MenuSectionLayout";
import { RecipesView } from "@/components/recipes/RecipesView";

// Внутренняя вкладка «Рецепты» раздела «Меню» (Этап 2).
// RecipesView читает состояние из URL query → нужен Suspense-границей.
export default function MenuRecipesPage() {
  return (
    <MenuSectionLayout subtitle="База блюд · поиск · подборки">
      <Suspense
        fallback={
          <div className="py-12 text-center text-sm text-graphite-400">Загрузка…</div>
        }
      >
        <RecipesView />
      </Suspense>
    </MenuSectionLayout>
  );
}
