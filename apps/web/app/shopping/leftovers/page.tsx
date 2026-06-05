import { Leftovers2026 } from "@/components/dom-2026/Leftovers2026";
import { MealLeftoversPage } from "@/components/menu/MealLeftoversPage";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

// Вкладка «Остатки» раздела «Покупки» (Этап 3).
export default function ShoppingLeftoversPage() {
  if (isPlanamUi2026Enabled()) {
    return <Leftovers2026 />;
  }
  return <MealLeftoversPage />;
}
