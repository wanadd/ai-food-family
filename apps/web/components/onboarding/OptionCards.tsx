import type { SelectOption } from "@/lib/onboarding/options";

type OptionCardsProps = {
  options: SelectOption[];
  value: string | null;
  onChange: (value: string) => void;
};

export function OptionCards({ options, value, onChange }: OptionCardsProps) {
  return (
    <div className="grid gap-3">
      {options.map((option) => {
        const selected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-2xl border px-4 py-4 text-left transition ${
              selected
                ? "border-emerald-600 bg-emerald-50 shadow-sm"
                : "border-stone-200 bg-white hover:border-stone-300"
            }`}
          >
            <span className="block text-base font-semibold text-stone-900">
              {option.label}
            </span>
            {option.hint ? (
              <span className="mt-1 block text-sm text-stone-500">{option.hint}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
