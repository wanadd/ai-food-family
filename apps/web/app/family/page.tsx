import { FamilyDashboard } from "@/components/family/FamilyDashboard";
import { redirectLegacyToPlanam2026 } from "@/lib/planam/planam-2026-page";

export default function FamilyPage() {
  redirectLegacyToPlanam2026("/account/family");
  return <FamilyDashboard />;
}
