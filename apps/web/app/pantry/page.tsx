import { redirect } from "next/navigation";

// Запасы переехали во вкладку раздела «Покупки» (Этап 3).
// Старый маршрут /pantry мягко ведёт на /shopping/pantry. Цикла нет:
// /shopping/pantry рендерит контент напрямую (без редиректа).
export default function PantryPage() {
  redirect("/shopping/pantry");
}
