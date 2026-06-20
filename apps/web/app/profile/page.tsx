import { ProfileDashboard } from "@/components/profile/ProfileDashboard";
import { redirectLegacyToPlanam2026 } from "@/lib/planam/planam-2026-page";

export default function ProfilePage() {
  redirectLegacyToPlanam2026("/account");
  return <ProfileDashboard />;
}
