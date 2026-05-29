import { redirect } from "next/navigation";

// Остатки блюд переехали во вкладку раздела «Покупки» (Этап 3).
// Старый маршрут /menu/leftovers мягко ведёт на /shopping/leftovers.
// Цикла нет: /shopping/leftovers рендерит контент напрямую.
export default function MenuLeftoversRoute() {
  redirect("/shopping/leftovers");
}
