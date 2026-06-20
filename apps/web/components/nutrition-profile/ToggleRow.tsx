type ToggleRowProps = {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
};

export function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: ToggleRowProps) {
  return (
    <label className="flex min-h-[48px] cursor-pointer items-center justify-between gap-3 rounded-control border border-cream-border bg-cream-deep/40 px-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-graphite-900">{label}</p>
        {description ? (
          <p className="mt-0.5 text-xs text-graphite-500">{description}</p>
        ) : null}
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-5 w-5 shrink-0 rounded border-cream-border text-sage-600 focus:ring-sage-400"
      />
    </label>
  );
}
