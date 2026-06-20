import { redirect } from "next/navigation";

// Уход/забота переехали в уведомления. Поведение сохранено из прежнего
// /nutritionist/care.
export default function HealthCarePage() {
  redirect("/notifications");
}
