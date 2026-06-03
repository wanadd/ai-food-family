import { cn } from "@/lib/planam/cn";

type OnboardingProgress2026Props = {
  step: number;
  total?: number;
};

export function OnboardingProgress2026({
  step,
  total = 6,
}: OnboardingProgress2026Props) {
  return (
    <div className="flex items-center justify-center gap-1.5 px-4 py-3" aria-hidden>
      {Array.from({ length: total }, (_, i) => (
        <span
          key={i}
          className={cn(
            "h-1.5 rounded-pill transition-all",
            i + 1 === step ? "w-6 bg-sage-500 dark:bg-sage-400" : "w-1.5 bg-pa-border",
            i + 1 < step && "bg-sage-300 dark:bg-sage-600",
          )}
        />
      ))}
    </div>
  );
}
