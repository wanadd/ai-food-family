import Link from "next/link";

import { RecipeCatalog } from "@/components/recipes/RecipeCatalog";

export default function MenuRecipesPage() {
  return (
    <div className="min-h-screen bg-stone-50 pb-24">
      <header className="border-b border-stone-100 bg-white px-4 py-3">
        <Link href="/menu" className="text-sm font-semibold text-emerald-700">
          ← Меню
        </Link>
        <h1 className="mt-1 text-lg font-bold text-stone-900">Каталог рецептов</h1>
        <p className="text-xs text-stone-500">
          Выбирайте сами — нутрициолог только подскажет
        </p>
      </header>
      <RecipeCatalog menuMode />
    </div>
  );
}
