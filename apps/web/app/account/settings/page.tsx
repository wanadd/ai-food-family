import {
  SettingsHub,
  SettingsMenuItem,
} from "@/components/settings/SettingsScaffold";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountSettingsPage() {
  requirePlanamUi2026OrRedirect("/account/settings");

  return (
    <SettingsHub>
      <SettingsMenuItem
        href="/account/settings/account"
        label="Аккаунт"
        description="Telegram, телефон, идентификатор"
      />
      <SettingsMenuItem
        href="/account/settings/documents"
        label="Документы"
        description="Соглашение, конфиденциальность, персональные данные"
      />
      <SettingsMenuItem
        href="/account/settings/delete-data"
        label="Удалить мои данные"
        description="Запрос на удаление"
      />
      <SettingsMenuItem
        href="/account/settings/support"
        label="Поддержка"
        description="Чат с ботом ПланАм"
      />
      <SettingsMenuItem
        href="/account/settings/about"
        label="О приложении"
        description="Версия и информация"
      />
    </SettingsHub>
  );
}
