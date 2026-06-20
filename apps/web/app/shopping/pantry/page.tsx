import { redirect } from "next/navigation";

import { PantryDashboard } from "@/components/pantry/PantryDashboard";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

// Вкладка «Запасы» раздела «Покупки» (Этап 3).
export default function ShoppingPantryPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/home/pantry");
  }
  return <PantryDashboard />;
}
