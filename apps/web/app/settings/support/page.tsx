import Link from "next/link";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;
const BOT_URL = BOT_USERNAME ? `https://t.me/${BOT_USERNAME}` : null;

const FAST_ACTIONS = [
  {
    title: "Написать в поддержку",
    description: "Вопрос по аккаунту, меню, покупкам или семье.",
  },
  {
    title: "Сообщить о проблеме",
    description: "Опишите экран, действие и что пошло не так.",
  },
  {
    title: "Предложить идею",
    description: "Что улучшить в меню, запасах или уведомлениях.",
  },
];

const FAQ = [
  {
    question: "Как работает меню?",
    answer: "PLANAM собирает меню из профиля питания, ограничений, запасов и выбранного режима.",
    href: "/plan/today",
  },
  {
    question: "Как работают покупки?",
    answer: "Список покупок собирается из выбранных рецептов и объединяет одинаковые продукты.",
    href: "/home/shopping",
  },
  {
    question: "Как учитывать ограничения?",
    answer: "Откройте профиль питания и добавьте аллергии, нелюбимые продукты, цели и бюджет.",
    href: "/account/nutrition",
  },
  {
    question: "Как работает семья?",
    answer: "Семейный режим хранит участников и учитывает их профили в общем меню.",
    href: "/account/family",
  },
  {
    question: "Что делать, если бот не отвечает?",
    answer: "Откройте чат с ботом заново и отправьте /start. Если не помогло, напишите в поддержку.",
    href: BOT_URL,
    external: true,
  },
];

export default function SettingsSupportPage() {
  return (
    <SettingsScaffold title="Поддержка" subtitle="Помощь и обратная связь">
      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <p className="text-sm leading-relaxed text-pa-muted">
          Быстрее всего связаться с поддержкой через Telegram. Если бот временно
          недоступен, оставьте экран открытым и попробуйте повторить позже.
        </p>
        {BOT_URL ? (
          <a
            href={BOT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex min-h-[44px] w-full items-center justify-center rounded-control bg-sage-600 px-4 py-2 text-sm font-semibold text-white shadow-soft transition active:scale-[0.99]"
          >
            Открыть @{BOT_USERNAME}
          </a>
        ) : (
          <p className="mt-4 rounded-control bg-cream-deep px-3 py-2 text-xs text-pa-muted dark:bg-pa-elevated">
            Поддержка подключается к Telegram-боту. В закрытом тесте напишите в
            чат, из которого открывали приложение.
          </p>
        )}
      </section>

      <section className="space-y-2">
        <div className="px-1">
          <h2 className="text-sm font-bold text-pa-foreground">Быстрые действия</h2>
          <p className="text-xs text-pa-muted">Все действия ведут в поддержку, без пустых кнопок.</p>
        </div>
        {FAST_ACTIONS.map((action) =>
          BOT_URL ? (
            <a
              key={action.title}
              href={BOT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.99] dark:shadow-none"
            >
              <p className="text-sm font-semibold text-pa-foreground">{action.title}</p>
              <p className="mt-1 text-xs leading-relaxed text-pa-muted">
                {action.description}
              </p>
            </a>
          ) : (
            <article
              key={action.title}
              className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none"
            >
              <p className="text-sm font-semibold text-pa-foreground">{action.title}</p>
              <p className="mt-1 text-xs leading-relaxed text-pa-muted">
                {action.description}
              </p>
            </article>
          ),
        )}
      </section>

      <section className="space-y-2">
        <div className="px-1">
          <h2 className="text-sm font-bold text-pa-foreground">Частые вопросы</h2>
        </div>
        {FAQ.map((item) => {
          const body = (
            <>
              <p className="text-sm font-semibold text-pa-foreground">{item.question}</p>
              <p className="mt-1 text-xs leading-relaxed text-pa-muted">{item.answer}</p>
            </>
          );
          if (!item.href) {
            return (
              <article
                key={item.question}
                className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none"
              >
                {body}
              </article>
            );
          }
          if (item.external) {
            return (
              <a
                key={item.question}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.99] dark:shadow-none"
              >
                {body}
              </a>
            );
          }
          return (
            <Link
              key={item.question}
              href={item.href}
              className="block rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.99] dark:shadow-none"
            >
              {body}
            </Link>
          );
        })}
      </section>
    </SettingsScaffold>
  );
}
