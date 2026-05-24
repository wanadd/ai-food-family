export type LeftoverStatus =
  | "active"
  | "frozen"
  | "consumed"
  | "discarded";

export const LEFTOVER_STATUS_OPTIONS: {
  value: LeftoverStatus;
  label: string;
}[] = [
  { value: "active", label: "Осталось" },
  { value: "consumed", label: "Съедено" },
  { value: "frozen", label: "Заморожено" },
  { value: "discarded", label: "Выброшено" },
];

export function leftoverStatusLabel(status: string): string {
  return (
    LEFTOVER_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status
  );
}
