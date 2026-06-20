import { cn } from "@/lib/planam/cn";

const MEAL_LABELS: Record<string, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};

type MealFallbackPlate2026Props = {
  mealType?: string;
  className?: string;
};

/** L1 fallback — тарелка по типу приёма пищи (без stock photo). */
export function MealFallbackPlate2026({
  mealType = "dinner",
  className,
}: MealFallbackPlate2026Props) {
  const label = MEAL_LABELS[mealType] ?? "Блюдо";

  return (
    <div
      className={cn(
        "flex h-full w-full flex-col items-center justify-center gap-2 bg-cream-deep dark:bg-graphite-700/40",
        className,
      )}
      aria-hidden
    >
      <svg className="size-16 text-sage-400 dark:text-sage-500" viewBox="0 0 64 64" fill="none">
        <ellipse cx="32" cy="36" rx="22" ry="14" stroke="currentColor" strokeWidth="2" />
        <path
          d="M18 28c4-8 12-12 14-12s10 4 14 12"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      <span className="pa26-caption text-pa-muted">{label}</span>
    </div>
  );
}
