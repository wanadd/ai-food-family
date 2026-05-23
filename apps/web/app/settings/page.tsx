import {
  SettingsHub,
  SettingsMenuItem,
} from "@/components/settings/SettingsScaffold";

export default function SettingsPage() {
  return (
    <SettingsHub>
      <SettingsMenuItem
        href="/settings/account"
        label="Аккаунт"
        description="Telegram, телефон, идентификатор"
      />
      <SettingsMenuItem
        href="/settings/care"
        label="Уведомления заботы"
        description="Мягкие подсказки в Telegram"
      />
      <SettingsMenuItem
        href="/settings/units"
        label="Единицы измерения"
        description="Граммы, литры, порции"
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
        href="/settings/privacy"
        label="Конфиденциальность"
        description="Данные и доступ"
      />
      <SettingsMenuItem
        href="/settings/language"
        label="Язык"
        description="Русский"
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
