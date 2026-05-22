"use client";

import { Sheet } from "@/components/ui/Sheet";

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
          <span className="text-xs font-semibold text-stone-500">Название</span>
          <input
            value={name}
            onChange={(event) => onNameChange(event.target.value)}
            required
            placeholder="Ремонт"
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={isFood}
            onChange={(event) => onIsFoodChange(event.target.checked)}
            className="h-4 w-4 rounded border-stone-300 text-emerald-600"
          />
          Это продукты?
        </label>
        <p className="text-xs text-stone-500">
          Если включено, купленные товары автоматически попадут в запасы.
        </p>
        <button
          type="submit"
          disabled={loading || !name.trim()}
          className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Создание…" : "Создать категорию"}
        </button>
      </form>
    </Sheet>
  );
}
