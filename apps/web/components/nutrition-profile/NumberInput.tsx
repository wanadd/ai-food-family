type NumberInputProps = {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
};

export function NumberInput({
  label,
  value,
  onChange,
  placeholder,
  min,
  max,
  step = 1,
  unit,
}: NumberInputProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-stone-700">
        {label}
      </span>
      <div className="relative">
        <input
          type="number"
          inputMode="decimal"
          value={value ?? ""}
          min={min}
          max={max}
          step={step}
          placeholder={placeholder}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === "") {
              onChange(null);
              return;
            }
            const parsed = step < 1 ? parseFloat(raw) : parseInt(raw, 10);
            onChange(Number.isNaN(parsed) ? null : parsed);
          }}
          className="w-full rounded-xl border border-stone-200 bg-white py-3 pl-4 pr-12 text-base text-stone-900 outline-none ring-emerald-500 focus:border-emerald-500 focus:ring-2"
        />
        {unit ? (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-stone-400">
            {unit}
          </span>
        ) : null}
      </div>
    </label>
  );
}
