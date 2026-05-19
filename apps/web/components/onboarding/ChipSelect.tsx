import type { SelectOption } from "@/lib/onboarding/options";

type ChipSelectProps = {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  multiple?: boolean;
  exclusiveNone?: string;
};

export function ChipSelect({
  options,
  value,
  onChange,
  multiple = true,
  exclusiveNone,
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
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const selected = value.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => toggle(option.value)}
            className={`rounded-full border px-4 py-2 text-left text-sm transition ${
              selected
                ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                : "border-stone-200 bg-white text-stone-700 hover:border-stone-300"
            }`}
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
