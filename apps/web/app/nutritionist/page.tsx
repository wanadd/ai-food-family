import { redirect } from "next/navigation";

// Раздел «Нутрициолог» переименован в «Здоровье». Мягкий redirect
// сохраняет работоспособность старых ссылок и Telegram deep-links.
export default function NutritionistRedirectPage() {
  redirect("/health");
}
