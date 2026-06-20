import { FamilyDashboard } from "@/components/family/FamilyDashboard";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountFamilyPage() {
  requirePlanamUi2026OrRedirect("/account/family");

  return <FamilyDashboard />;
}
