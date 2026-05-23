import type { MemberProgressStatus } from "./types";

export const STATUS_LABELS: Record<MemberProgressStatus, string> = {
  improving: "Улучшается",
  stable: "Стабильно",
  attention: "Требует внимания",
  hidden: "Скрыто",
};

export function formatWeightKg(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toFixed(1)} кг`;
}

export function formatWeightDelta(value: number | null | undefined): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)} кг`;
}

export function formatWater(ml: number | null | undefined): string {
  if (ml == null) return "—";
  if (ml >= 1000) return `${(ml / 1000).toFixed(1)} л`;
  return `${ml} мл`;
}
