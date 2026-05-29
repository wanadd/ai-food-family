"use client";

type FilterChipProps = {
  label: string;
  active: boolean;
  onClick: () => void;
};

/** Переиспользуемая «таблетка»-фильтр каталога рецептов. */
export function FilterChip({ label, active, onClick }: FilterChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`shrink-0 rounded-pill px-3 py-1.5 text-xs font-semibold transition ${
        active
          ? "bg-sage-500 text-white"
          : "bg-cream-surface text-graphite-700 ring-1 ring-cream-border hover:bg-sage-50"
      }`}
    >
      {label}
    </button>
  );
}
