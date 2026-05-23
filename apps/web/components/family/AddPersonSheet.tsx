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
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
      <button
        type="button"
        className="absolute inset-0"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div className="relative w-full max-w-lg rounded-t-3xl bg-white p-5 shadow-xl sm:rounded-3xl">
        <h2 className="text-lg font-bold text-stone-900">Добавить человека</h2>
        <p className="mt-1 text-sm text-stone-500">Выберите способ</p>

        <div className="mt-4 space-y-2">
          <button
            type="button"
            onClick={() => {
              onClose();
              onInviteTelegram();
            }}
            className="flex w-full min-h-[56px] flex-col items-start rounded-2xl border border-stone-100 bg-white px-4 py-3.5 text-left shadow-sm transition hover:border-violet-200 active:scale-[0.99]"
          >
            <span className="font-semibold text-stone-900">
              Пригласить в Telegram
            </span>
            <span className="mt-0.5 text-sm text-stone-500">
              Человек сам настроит профиль питания
            </span>
          </button>
          <button
            type="button"
            onClick={() => {
              onClose();
              onAddVirtual();
            }}
            className="flex w-full min-h-[56px] flex-col items-start rounded-2xl border border-stone-100 bg-white px-4 py-3.5 text-left shadow-sm transition hover:border-emerald-200 active:scale-[0.99]"
          >
            <span className="font-semibold text-stone-900">
              Без аккаунта Telegram
            </span>
            <span className="mt-0.5 text-sm text-stone-500">
              Ребёнок, родственник — профиль заполняет админ
            </span>
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-4 w-full rounded-2xl border border-stone-200 py-3 text-sm font-semibold text-stone-700"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
