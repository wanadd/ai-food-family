import type { ReactNode } from "react";

import {
  SettingsHub,
  SettingsMenuItem,
} from "@/components/settings/SettingsScaffold";
import { ThemeToggle2026 } from "@/components/planam-2026/theme/ThemeToggle2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-2">
      <div className="px-1">
        <h2 className="text-sm font-bold text-pa-foreground">{title}</h2>
        {description ? <p className="text-xs text-pa-muted">{description}</p> : null}
      </div>
      <div className="space-y-2">{children}</div>
    </section>
  );
}

export default function AccountSettingsPage() {
  requirePlanamUi2026OrRedirect("/account/settings");

  return (
    <SettingsHub>
      <SettingsSection
        title="Внешний вид"
        description="Тема применяется ко всему Mini App."
      >
        <div className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
          <p className="text-sm font-semibold text-pa-foreground">Тема</p>
          <p className="mt-0.5 text-xs text-pa-muted">
            Светлая, тёмная или как в системе.
          </p>
          <div className="mt-3">
            <ThemeToggle2026 />
          </div>
        </div>
      </SettingsSection>

      <SettingsSection
        title="Аккаунт"
        description="Профиль, семья и питание остаются внутри account stack."
      >
        <SettingsMenuItem
          href="/account/settings/account"
          label="Профиль"
          description="Telegram, телефон и идентификатор"
        />
        <SettingsMenuItem
          href="/account/family"
          label="Семья"
          description="Участники, роли и приглашения"
        />
        <SettingsMenuItem
          href="/account/nutrition"
          label="Питание"
          description="Ограничения, аллергии, цели и бюджет"
        />
      </SettingsSection>

      <SettingsSection title="Приложение">
        <SettingsMenuItem
          href="/account/settings/support"
          label="Поддержка"
          description="Помощь, проблема или идея"
        />
        <SettingsMenuItem
          href="/account/settings/documents"
          label="Документы"
          description="Соглашение, конфиденциальность и подписка"
        />
        <SettingsMenuItem
          href="/account/settings/about"
          label="О PLANAM"
          description="Статус закрытого тестирования и версия"
        />
      </SettingsSection>

      <SettingsSection title="Безопасность">
        <SettingsMenuItem
          href="/account/settings/delete-data"
          label="Удалить мои данные"
          description="Запрос на удаление аккаунта"
        />
      </SettingsSection>
    </SettingsHub>
  );
}
