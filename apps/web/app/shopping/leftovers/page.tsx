import { LeftoversV2 } from "@/components/planam-v2/home-domain/LeftoversV2";
import { MealLeftoversPage } from "@/components/menu/MealLeftoversPage";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

// Вкладка «Остатки» раздела «Покупки» (Этап 3).
export default function ShoppingLeftoversPage() {
  if (isPlanamUi2026Enabled()) {
    return <LeftoversV2 />;
  }
  return <MealLeftoversPage />;
}
