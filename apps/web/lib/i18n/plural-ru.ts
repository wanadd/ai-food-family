/** Russian plural forms: one (1, 21…), few (2–4, 22–24…), many (0, 5–20, 25…). */
export function pluralRu(
  count: number,
  one: string,
  few: string,
  many: string,
): string {
  const n = Math.abs(Math.trunc(count));
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 14) return many;
  if (mod10 === 1) return one;
  if (mod10 >= 2 && mod10 <= 4) return few;
  return many;
}

export function pluralRuWithCount(
  count: number,
  one: string,
  few: string,
  many: string,
): string {
  return `${count} ${pluralRu(count, one, few, many)}`;
}
