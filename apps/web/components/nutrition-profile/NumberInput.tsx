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
      <span className="mb-1.5 block text-sm font-medium text-graphite-700">
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
          className="w-full rounded-control border border-cream-border bg-cream-surface py-3 pl-4 pr-12 text-base text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
        />
        {unit ? (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-graphite-400">
            {unit}
          </span>
        ) : null}
      </div>
    </label>
  );
}
