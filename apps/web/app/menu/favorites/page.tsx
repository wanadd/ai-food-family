import { redirect } from "next/navigation";

// Скелет внутренней вкладки «Избранное». Контент переедет в Этапе 2.
// Пока временный мягкий redirect на действующий каталог рецептов.
export default function MenuFavoritesPage() {
  redirect("/recipes");
}
