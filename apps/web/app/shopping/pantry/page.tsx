import { redirect } from "next/navigation";

// Скелет внутренней вкладки «Запасы» внутри раздела «Покупки».
// Контент переедет в Этапе 3. Пока временный мягкий redirect на
// действующий экран запасов.
export default function ShoppingPantryPage() {
  redirect("/pantry");
}
