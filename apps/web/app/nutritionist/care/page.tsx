import { redirect } from "next/navigation";

// Переехало в /health/care. Мягкий redirect сохраняет старые ссылки.
export default function NutritionistCareRedirectPage() {
  redirect("/health/care");
}
