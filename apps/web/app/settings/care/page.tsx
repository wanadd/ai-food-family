import Link from "next/link";

import { CareTelegramBlock } from "@/components/care/CareTelegramBlock";
import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

export default function CareSettingsPage() {
  return (
    <SettingsScaffold
      title="Уведомления заботы"
      subtitle="ПланАм будет мягко напоминать о важном"
    >
      <p className="text-sm leading-relaxed text-stone-600">
        Сообщения приходят в ваш чат с ботом ПланАм в Telegram. Мы не отправляем
        одинаковые напоминания слишком часто и учитываем тихие часы, если вы их
        зададите позже.
      </p>

      <CareTelegramBlock compact showSettingsLink={false} />

      <p className="text-center text-sm text-stone-500">
        <Link href="/notifications" className="font-semibold text-emerald-700">
          Напоминания о покупках и готовке
        </Link>
      </p>
    </SettingsScaffold>
  );
}
