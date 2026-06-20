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
      <div className="relative w-full max-w-lg rounded-t-card bg-cream-surface p-5 shadow-lift sm:rounded-card">
        <h2 className="text-lg font-bold text-graphite-900">Добавить человека</h2>
        <p className="mt-1 text-sm text-graphite-500">Выберите способ</p>

        <div className="mt-4 space-y-2">
          <button
            type="button"
            onClick={() => {
              onClose();
              onInviteTelegram();
            }}
            data-testid="family-invite-member"
            className="pa-card flex w-full min-h-[56px] flex-col items-start px-4 py-3.5 text-left transition hover:border-sage-200 active:scale-[0.99]"
          >
            <span className="font-semibold text-graphite-900">
              Пригласить в Telegram
            </span>
            <span className="mt-0.5 text-sm text-graphite-500">
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
            className="pa-card flex w-full min-h-[56px] flex-col items-start px-4 py-3.5 text-left transition hover:border-sage-200 active:scale-[0.99]"
          >
            <span className="font-semibold text-graphite-900">
              Без аккаунта Telegram
            </span>
            <span className="mt-0.5 text-sm text-graphite-500">
              Ребёнок, родственник — профиль заполняет админ
            </span>
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="pa-btn-ghost mt-4 w-full"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
