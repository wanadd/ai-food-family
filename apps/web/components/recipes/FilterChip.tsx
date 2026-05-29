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
      className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
        active
          ? "bg-emerald-600 text-white"
          : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50"
      }`}
    >
      {label}
    </button>
  );
}
