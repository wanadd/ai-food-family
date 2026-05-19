type StepNavigationProps = {
  canGoBack: boolean;
  canGoNext: boolean;
  isLastStep: boolean;
  isWelcome: boolean;
  saving: boolean;
  onBack: () => void;
  onNext: () => void;
};

export function StepNavigation({
  canGoBack,
  canGoNext,
  isLastStep,
  isWelcome,
  saving,
  onBack,
  onNext,
}: StepNavigationProps) {
  return (
    <div className="flex gap-3">
      {canGoBack ? (
        <button
          type="button"
          onClick={onBack}
          disabled={saving}
          className="flex-1 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm font-semibold text-stone-700 transition hover:bg-stone-50 disabled:opacity-50"
        >
          Назад
        </button>
      ) : (
        <div className="flex-1" />
      )}
      <button
        type="button"
        onClick={onNext}
        disabled={saving || !canGoNext}
        className="flex-[1.4] rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving
          ? "Сохранение…"
          : isWelcome
            ? "Начать"
            : isLastStep
              ? "Завершить"
              : "Далее"}
      </button>
    </div>
  );
}
