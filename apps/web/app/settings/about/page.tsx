import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

const APP_VERSION = "0.1.0";

export default function SettingsAboutPage() {
  return (
    <SettingsScaffold title="О приложении" subtitle="ПланАм">
      <section className="rounded-2xl border border-emerald-100 bg-gradient-to-b from-emerald-50/80 to-white p-5 shadow-sm">
        <p className="text-2xl font-bold text-stone-900">ПланАм</p>
        <p className="mt-1 text-sm font-medium text-emerald-700">
          Питайся с умом
        </p>
        <p className="mt-4 text-sm leading-relaxed text-stone-600">
          AI-помощник по питанию, покупкам, запасам и целям. Работает в Telegram
          для одного человека, пары или семьи.
        </p>
        <p className="mt-4 text-xs text-stone-500">Версия {APP_VERSION}</p>
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <ul className="space-y-2 text-sm text-stone-600">
          <li>Меню с учётом целей и запасов</li>
          <li>Универсальный список покупок</li>
          <li>Запасы и остатки блюд</li>
          <li>Нутрициолог и PRO — в разработке</li>
        </ul>
      </section>
    </SettingsScaffold>
  );
}
