import type { SelectOption } from "@/lib/onboarding/options";

type OptionCardsProps = {
  options: SelectOption[];
  value: string | null;
  onChange: (value: string) => void;
  compact?: boolean;
};

export function OptionCards({
  options,
  value,
  onChange,
  compact = false,
}: OptionCardsProps) {
  return (
    <div className={compact ? "grid gap-2" : "grid gap-3"}>
      {options.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={
              compact
                ? `rounded-control border px-3 py-2.5 text-left transition ${
                    selected
                      ? "border-sage-600 bg-sage-50 shadow-sm dark:border-sage-500 dark:bg-sage-900/20"
                      : "border-pa-border bg-pa-surface hover:bg-sage-50 dark:hover:bg-pa-elevated/40"
                  }`
                : `rounded-2xl border px-4 py-4 text-left transition ${
                    selected
                      ? "border-emerald-600 bg-emerald-50 shadow-sm"
                      : "border-stone-200 bg-white hover:border-stone-300"
                  }`
            }
          >
            <span
              className={
                compact
                  ? "block text-sm font-semibold text-pa-foreground"
                  : "block text-base font-semibold text-stone-900"
              }
            >
              {option.label}
            </span>
            {option.hint ? (
              <span
                className={
                  compact
                    ? "mt-0.5 block text-xs text-pa-muted"
                    : "mt-1 block text-sm text-stone-500"
                }
              >
                {option.hint}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
