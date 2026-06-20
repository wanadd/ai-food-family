import { AccountHub2026 } from "@/components/planam-2026/account/AccountHub2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountPage() {
  requirePlanamUi2026OrRedirect("/account");

  return <AccountHub2026 />;
}
