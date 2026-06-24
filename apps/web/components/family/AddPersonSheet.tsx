"use client";

type AddPersonSheetProps = {
  open: boolean;
  onClose: () => void;
  onInviteTelegram: () => void;
  onAddVirtual: () => void;
};

export function AddPersonSheet({
  open,
  onClose,
  onInviteTelegram,
  onAddVirtual,
}: AddPersonSheetProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/40 p-0 sm:items-center sm:p-4">
      <button
        type="button"
        className="absolute inset-0"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div className="relative w-full max-w-lg rounded-t-card border border-pa-border bg-pa-surface p-5 shadow-lift sm:rounded-card">
        <h2 className="text-lg font-bold text-pa-foreground">Добавить человека</h2>
        <p className="mt-1 text-sm text-pa-muted">Выберите понятный способ добавления</p>

        <div className="mt-4 space-y-2">
          <button
            type="button"
            onClick={() => {
              onClose();
              onInviteTelegram();
            }}
            data-testid="family-invite-member"
            className="flex w-full min-h-[64px] flex-col items-start rounded-card border border-pa-border bg-pa-surface px-4 py-3.5 text-left shadow-soft transition hover:bg-sage-50 active:scale-[0.99] dark:shadow-none"
          >
            <span className="font-semibold text-pa-foreground">
              Пригласить в Telegram
            </span>
            <span className="mt-0.5 text-sm text-pa-muted">
              Человек сам настроит профиль питания
            </span>
          </button>
          <button
            type="button"
            onClick={() => {
              onClose();
              onAddVirtual();
            }}
            data-testid="family-add-virtual-member"
            className="flex w-full min-h-[64px] flex-col items-start rounded-card border border-pa-border bg-pa-surface px-4 py-3.5 text-left shadow-soft transition hover:bg-sage-50 active:scale-[0.99] dark:shadow-none"
          >
            <span className="font-semibold text-pa-foreground">
              Без аккаунта Telegram
            </span>
            <span className="mt-0.5 text-sm text-pa-muted">
              Ребёнок, родственник — профиль заполняет админ
            </span>
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-4 min-h-[44px] w-full rounded-control border border-pa-border bg-pa-surface px-4 py-2 text-sm font-semibold text-pa-foreground"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
