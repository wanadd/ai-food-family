import { redirect } from "next/navigation";

import { MenuCurrentView } from "@/components/menu/MenuCurrentView";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";

export default function MenuCurrentPage() {
  if (isPlanamUi2026Enabled()) {
    redirect(PLAN_PATHS.today);
  }
  return <MenuCurrentView />;
}
