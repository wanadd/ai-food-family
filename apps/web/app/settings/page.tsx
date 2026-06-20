import {
  SettingsHub,
  SettingsMenuItem,
} from "@/components/settings/SettingsScaffold";
import { redirectLegacyToPlanam2026 } from "@/lib/planam/planam-2026-page";

export default function SettingsPage() {
  redirectLegacyToPlanam2026("/account/settings");
  return (
    <SettingsHub>
      <SettingsMenuItem
        href="/settings/account"
        label="Аккаунт"
        description="Telegram, телефон, идентификатор"
      />
      <SettingsMenuItem
        href="/settings/documents"
        label="Документы"
        description="Соглашение, конфиденциальность, персональные данные"
      />
      <SettingsMenuItem
        href="/settings/delete-data"
        label="Удалить мои данные"
        description="Запрос на удаление"
      />
      <SettingsMenuItem
        href="/settings/support"
        label="Поддержка"
        description="Чат с ботом ПланАм"
      />
      <SettingsMenuItem
        href="/settings/about"
        label="О приложении"
        description="Версия и информация"
      />
    </SettingsHub>
  );
}
