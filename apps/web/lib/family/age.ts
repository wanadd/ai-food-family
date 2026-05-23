const MAX_AGE_MONTHS = 130 * 12;

export type AgeUnit = "months" | "years";

export function toAgeMonths(amount: number, unit: AgeUnit): number {
  if (unit === "months") return amount;
  return amount * 12;
}

export function defaultAgeUnit(
  isChild: boolean,
  ageMonths: number | null | undefined,
): AgeUnit {
  if (ageMonths != null && ageMonths < 24) return "months";
  if (isChild && ageMonths == null) return "months";
  return "years";
}

export function ageInputFromMonths(
  ageMonths: number | null | undefined,
  isChild: boolean,
): { amount: number | null; unit: AgeUnit } {
  if (ageMonths == null) {
    return { amount: null, unit: defaultAgeUnit(isChild, null) };
  }
  const unit = defaultAgeUnit(isChild, ageMonths);
  if (unit === "months") {
    return { amount: ageMonths, unit: "months" };
  }
  if (ageMonths % 12 === 0) {
    return { amount: ageMonths / 12, unit: "years" };
  }
  return { amount: ageMonths, unit: "months" };
}

export function validateAgeMonths(
  ageMonths: number | null,
  isChild: boolean,
): string | null {
  if (ageMonths == null || Number.isNaN(ageMonths)) {
    return "Укажите возраст";
  }
  if (ageMonths < 0) return "Возраст не может быть отрицательным";
  if (ageMonths > MAX_AGE_MONTHS) return "Слишком большой возраст";
  if (isChild && ageMonths > 18 * 12) {
    return "Для ребёнка укажите возраст до 18 лет";
  }
  return null;
}

function yearsWord(n: number): string {
  const abs = Math.abs(n);
  if (abs % 10 === 1 && abs % 100 !== 11) return `${n} год`;
  if (abs % 10 >= 2 && abs % 10 <= 4 && (abs % 100 < 10 || abs % 100 >= 20)) {
    return `${n} года`;
  }
  return `${n} лет`;
}

function monthsWord(n: number): string {
  const abs = Math.abs(n);
  if (abs % 10 === 1 && abs % 100 !== 11) return `${n} месяц`;
  if (abs % 10 >= 2 && abs % 10 <= 4 && (abs % 100 < 10 || abs % 100 >= 20)) {
    return `${n} месяца`;
  }
  return `${n} месяцев`;
}

export function formatAgeMonthsRu(ageMonths: number | null | undefined): string {
  if (ageMonths == null) return "—";
  const years = Math.floor(ageMonths / 12);
  const months = ageMonths % 12;
  if (years === 0) return monthsWord(months);
  if (months === 0) return yearsWord(years);
  return `${yearsWord(years)} ${monthsWord(months)}`;
}
