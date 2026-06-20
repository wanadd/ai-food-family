import { redirect } from "next/navigation";

// «Сценарии» и «Из запасов» НЕ являются отдельными вкладками — это фильтры
// и подборки внутри Рецептов. Маршрут существует для совместимости и мягко
// ведёт на вкладку «Рецепты».
export default function MenuScenariosPage() {
  redirect("/menu/recipes");
}
