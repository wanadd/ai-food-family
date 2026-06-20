"use client";

import { Sheet } from "@/components/ui/Sheet";

const INPUT_CLS =
  "mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200";

type ShoppingCategorySheetProps = {
  open: boolean;
  name: string;
  isFood: boolean;
  onNameChange: (name: string) => void;
  onIsFoodChange: (value: boolean) => void;
  onClose: () => void;
  onSubmit: () => void;
  loading?: boolean;
};

export function ShoppingCategorySheet({
  open,
  name,
  isFood,
  onNameChange,
  onIsFoodChange,
  onClose,
  onSubmit,
  loading = false,
}: ShoppingCategorySheetProps) {
  return (
    <Sheet open={open} title="Новая категория" onClose={onClose}>
      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <label className="block">
          <span className="text-xs font-semibold text-graphite-500">Название</span>
          <input
            value={name}
            onChange={(event) => onNameChange(event.target.value)}
            required
            placeholder="Ремонт"
            className={INPUT_CLS}
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-graphite-700">
          <input
            type="checkbox"
            checked={isFood}
            onChange={(event) => onIsFoodChange(event.target.checked)}
            className="h-4 w-4 rounded border-cream-border text-sage-500"
          />
          Это продукты?
        </label>
        <p className="text-xs text-graphite-500">
          Если включено, купленные товары автоматически попадут в запасы.
        </p>
        <button
          type="submit"
          disabled={loading || !name.trim()}
          className="pa-btn-primary w-full disabled:opacity-50"
        >
          {loading ? "Создание…" : "Создать категорию"}
        </button>
      </form>
    </Sheet>
  );
}
