import { AmsHub2026 } from "@/components/monetization-2026/AmsHub2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountAmsPage() {
  requirePlanamUi2026OrRedirect("/account/ams");

  return <AmsHub2026 />;
}
