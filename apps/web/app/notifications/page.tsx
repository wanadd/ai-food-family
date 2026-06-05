import { NotificationsView } from "@/components/notifications/NotificationsView";
import { redirectLegacyToPlanam2026 } from "@/lib/planam/planam-2026-page";

export default function NotificationsPage() {
  redirectLegacyToPlanam2026("/account/notifications");

  return <NotificationsView />;
}
