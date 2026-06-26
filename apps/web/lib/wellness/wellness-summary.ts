import type { ProgressOverview } from "@/lib/progress/types";

export function buildWellnessSummaryPhrase(
  progress: ProgressOverview | null,
): string | null {
  const targets = progress?.targets;
  const actual = progress?.daily_actual;
  if (!targets || !actual?.meals_logged) {
    return null;
  }

  const parts: string[] = [];

  const calTarget = targets.calories_target;
  const calEaten = actual.calories_consumed ?? 0;
  if (calTarget != null && calTarget > calEaten) {
    parts.push(`${Math.round(calTarget - calEaten)} ккал`);
  }

  const proteinTarget = targets.protein_target_g;
  const proteinEaten = actual.protein_consumed_g ?? 0;
  if (proteinTarget != null && proteinTarget > proteinEaten) {
    parts.push(`${Math.round(proteinTarget - proteinEaten)} г белка`);
  }

  if (parts.length === 0) {
    return "План на сегодня выполнен";
  }

  return `Осталось ${parts.join(" и ")}`;
}
