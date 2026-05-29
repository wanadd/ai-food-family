import { redirect } from "next/navigation";

// Скелет внутренней вкладки «Коллекции». Контент переедет в Этапе 2
// (данные коллекций уже есть в lib/recipes/api.ts). Пока временный
// мягкий redirect на действующий каталог рецептов.
export default function MenuCollectionsPage() {
  redirect("/recipes");
}
