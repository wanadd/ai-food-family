import { NotificationsView } from "@/components/notifications/NotificationsView";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountNotificationsPage() {
  requirePlanamUi2026OrRedirect("/account/notifications");

  return <NotificationsView />;
}
