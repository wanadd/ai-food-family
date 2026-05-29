import { redirect } from "next/navigation";

// Каталог рецептов переехал во внутреннюю вкладку раздела «Меню» (Этап 2).
// Старый маршрут /recipes мягко ведёт на новую вкладку «Рецепты».
export default function RecipesPage() {
  redirect("/menu/recipes");
}
