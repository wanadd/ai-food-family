import type { SelectOption } from "@/lib/onboarding/options";

type ChipSelectProps = {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  multiple?: boolean;
  exclusiveNone?: string;
  compact?: boolean;
};

export function ChipSelect({
  options,
  value,
  onChange,
  multiple = true,
  exclusiveNone,
  compact = false,
}: ChipSelectProps) {
  function toggle(optionValue: string) {
    if (!multiple) {
      onChange([optionValue]);
      return;
    }

    if (exclusiveNone && optionValue === exclusiveNone) {
      onChange(value.includes(optionValue) ? [] : [optionValue]);
      return;
    }

    const withoutNone = exclusiveNone
      ? value.filter((item) => item !== exclusiveNone)
      : [...value];

    if (withoutNone.includes(optionValue)) {
      onChange(withoutNone.filter((item) => item !== optionValue));
      return;
    }

    onChange([...withoutNone, optionValue]);
  }

  return (
    <div className={compact ? "flex flex-wrap gap-1.5" : "flex flex-wrap gap-2"}>
      {options.map((option) => {
        const selected = value.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => toggle(option.value)}
            className={
              compact
                ? `rounded-pill border px-3 py-1.5 text-left text-xs transition ${
                    selected
                      ? "border-sage-600 bg-sage-50 text-sage-900 dark:border-sage-500 dark:bg-sage-900/20 dark:text-sage-200"
                      : "border-pa-border bg-pa-surface text-pa-muted hover:bg-sage-50 dark:hover:bg-pa-elevated/40"
                  }`
                : `rounded-full border px-4 py-2 text-left text-sm transition ${
                    selected
                      ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                      : "border-stone-200 bg-white text-stone-700 hover:border-stone-300"
                  }`
            }
          >
            <span className="font-medium">{option.label}</span>
            {option.hint ? (
              <span className="mt-0.5 block text-xs opacity-70">{option.hint}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
