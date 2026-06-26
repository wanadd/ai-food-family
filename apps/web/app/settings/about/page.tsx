import Link from "next/link";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

const APP_VERSION = "0.1.0";

const PRODUCT_POINTS = [
  "Меню на день и неделю с учётом целей питания.",
  "Список покупок, запасы и остатки блюд в одном контуре.",
  "Семейные профили, ограничения и мягкие напоминания.",
  "AI-нутрициолог и Pro-сценарии развиваются как будущий scaffold.",
];

export default function SettingsAboutPage() {
  return (
    <SettingsScaffold title="О PLANAM" subtitle="Семейный AI-помощник по питанию">
      <section className="rounded-card border border-sage-100 bg-gradient-to-b from-sage-50/80 to-pa-surface p-5 shadow-soft dark:border-sage-700/40 dark:from-sage-900/20 dark:to-pa-surface dark:shadow-none">
        <span className="rounded-pill bg-sage-600 px-3 py-1 text-xs font-bold text-white">
          PLANAM
        </span>
        <h2 className="mt-4 text-2xl font-bold text-pa-foreground">PLANAM</h2>
        <p className="mt-2 text-sm leading-relaxed text-pa-muted">
          PLANAM помогает семье планировать питание, готовить по понятным
          рецептам, собирать покупки и учитывать ограничения без ручной рутины.
        </p>
      </section>

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">Что уже есть в продукте</h2>
        <ul className="mt-3 space-y-2">
          {PRODUCT_POINTS.map((point) => (
            <li key={point} className="flex gap-2 text-sm leading-relaxed text-pa-muted">
              <span className="mt-1 size-1.5 shrink-0 rounded-full bg-sage-500" aria-hidden />
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="grid gap-2">
        <Link
          href="/account/settings/documents"
          className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.99] dark:shadow-none"
        >
          <p className="text-sm font-semibold text-pa-foreground">Документы</p>
          <p className="mt-1 text-xs text-pa-muted">
            Соглашение, конфиденциальность и подписка.
          </p>
        </Link>
        <Link
          href="/account/settings/support"
          className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.99] dark:shadow-none"
        >
          <p className="text-sm font-semibold text-pa-foreground">Поддержка</p>
          <p className="mt-1 text-xs text-pa-muted">
            Вопрос, проблема или идея для команды.
          </p>
        </Link>
      </section>

      <p className="px-1 text-xs text-pa-muted">Версия приложения: {APP_VERSION}</p>
    </SettingsScaffold>
  );
}
