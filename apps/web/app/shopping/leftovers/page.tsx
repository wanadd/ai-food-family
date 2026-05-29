import { redirect } from "next/navigation";

// Скелет внутренней вкладки «Остатки» внутри раздела «Покупки».
// Контент переедет в Этапе 3. Пока временный мягкий redirect на
// действующий экран остатков блюд.
export default function ShoppingLeftoversPage() {
  redirect("/menu/leftovers");
}
