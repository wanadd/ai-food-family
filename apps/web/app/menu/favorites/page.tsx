import { MenuSectionLayout } from "@/components/menu/MenuSectionLayout";
import { FavoritesView } from "@/components/recipes/FavoritesView";

// Внутренняя вкладка «Избранное» раздела «Меню» (Этап 2).
export default function MenuFavoritesPage() {
  return (
    <MenuSectionLayout subtitle="Сохранённые рецепты">
      <FavoritesView />
    </MenuSectionLayout>
  );
}
