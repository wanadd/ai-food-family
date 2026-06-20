import { MenuSectionLayout } from "@/components/menu/MenuSectionLayout";
import { CollectionsView } from "@/components/recipes/CollectionsView";

// Внутренняя вкладка «Коллекции» раздела «Меню» (Этап 2, минимальный UI).
export default function MenuCollectionsPage() {
  return (
    <MenuSectionLayout subtitle="Ваши подборки рецептов">
      <CollectionsView />
    </MenuSectionLayout>
  );
}
