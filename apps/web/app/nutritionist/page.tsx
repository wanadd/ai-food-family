import { BottomBackButton } from "@/components/layout/BottomBackButton";

export default function NutritionistPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="px-5 pb-2 pt-8">
        <h1 className="text-2xl font-bold text-stone-900">AI-нутрициолог</h1>
      </header>

      <main className="mx-auto max-w-lg px-5 pb-4">
        <section className="rounded-3xl border border-emerald-100 bg-emerald-50/50 p-6 shadow-sm">
          <p className="text-lg font-semibold text-stone-900">
            AI-нутрициолог скоро будет доступен
          </p>
          <p className="mt-3 text-sm leading-relaxed text-stone-600">
            Здесь будут рекомендации по питанию, целям, БЖУ и привычкам.
          </p>
        </section>
      </main>

      <BottomBackButton className="pb-2 pt-4" />
    </div>
  );
}
