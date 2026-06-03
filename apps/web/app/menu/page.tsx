import { redirect } from "next/navigation";

import { MenuHub } from "@/components/menu/MenuHub";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";

export default function MenuPage() {
  if (isPlanamUi2026Enabled()) {
    redirect(PLAN_PATHS.week);
  }
  return <MenuHub />;
}
