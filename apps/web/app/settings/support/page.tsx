import Link from "next/link";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;
const BOT_URL = BOT_USERNAME ? `https://t.me/${BOT_USERNAME}` : null;

export default function SettingsSupportPage() {
  return (
    <SettingsScaffold title="Поддержка" subtitle="Помощь и обратная связь">
      <section className="rounded-2xl border border-stone-100 bg-white p-5 shadow-sm">
        <p className="text-sm leading-relaxed text-stone-600">
          По вопросам работы ПланАм, приглашениям в семью и подтверждению телефона
          удобнее всего написать в чат с ботом в Telegram.
        </p>
        {BOT_URL ? (
          <a
            href={BOT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex min-h-[48px] items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-center text-sm font-semibold text-white shadow-md shadow-emerald-200/50 transition hover:bg-emerald-700 active:scale-[0.99]"
          >
            Открыть @{BOT_USERNAME}
          </a>
        ) : (
          <p className="mt-4 text-sm text-stone-500">
            Укажите NEXT_PUBLIC_TELEGRAM_BOT_USERNAME в настройках приложения.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-5 shadow-sm">
        <p className="font-semibold text-stone-900">Частые вопросы</p>
        <ul className="mt-3 space-y-3 text-sm text-stone-600">
          <li>
            <span className="font-medium text-stone-800">Нет телефона в профиле</span>
            — отправьте контакт боту через /start.
          </li>
          <li>
            <span className="font-medium text-stone-800">Семейный режим</span>
            — создайте семью в разделе «Семья и участники».
          </li>
          <li>
            <span className="font-medium text-stone-800">Уведомления</span>
            — настройте в разделе{" "}
            <Link href="/notifications" className="font-semibold text-emerald-700">
              Уведомления
            </Link>
            .
          </li>
        </ul>
      </section>
    </SettingsScaffold>
  );
}
