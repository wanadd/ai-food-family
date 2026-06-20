import { redirect } from "next/navigation";

import { MenuPlanner } from "@/components/menu/MenuPlanner";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";

export default function MenuGeneratePage() {
  if (isPlanamUi2026Enabled()) {
    redirect(PLAN_PATHS.generate);
  }
  return <MenuPlanner />;
}
