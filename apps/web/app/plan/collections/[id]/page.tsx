import { redirect } from "next/navigation";

import { PLANAM_ROUTES } from "@/lib/planam/routes";

export default function PlanCollectionDetailPage() {
  redirect(PLANAM_ROUTES.planCollections);
}
