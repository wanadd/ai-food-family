"use client";

import { buildMiniAppUrl } from "@/lib/telegram";

export function OpenMiniAppButton() {
  const miniAppUrl = buildMiniAppUrl();

  if (!miniAppUrl) {
    return (
      <p className="text-sm text-amber-700">
        Укажите <code className="text-xs">NEXT_PUBLIC_TELEGRAM_BOT_USERNAME</code>{" "}
        в <code className="text-xs">apps/web/.env.local</code>, чтобы показать
        кнопку открытия Mini App.
      </p>
    );
  }

  return (
    <a
      href={miniAppUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center rounded-xl bg-[#2AABEE] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#229ED9]"
    >
      Открыть Mini App в Telegram
    </a>
  );
}
