import { redirect } from "next/navigation";

// Скелет внутренней вкладки «Рецепты». Контент переедет в Этапе 2.
// Пока временный мягкий redirect на действующий каталог.
export default function MenuRecipesPage() {
  redirect("/recipes");
}
