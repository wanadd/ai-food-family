import { redirect } from "next/navigation";

import HealthChatPageClient from "./HealthChatPageClient";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function HealthChatPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/wellness/chat");
  }
  return <HealthChatPageClient />;
}
