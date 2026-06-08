import { redirect } from "next/navigation";

import { PLANAM_ROUTES } from "@/lib/planam/routes";

export default function WellnessProgressPage() {
  redirect(PLANAM_ROUTES.wellness);
}
