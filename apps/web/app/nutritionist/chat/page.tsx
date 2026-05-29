import { redirect } from "next/navigation";

// Переехало в /health/chat. Мягкий redirect сохраняет старые ссылки.
export default function NutritionistChatRedirectPage() {
  redirect("/health/chat");
}
