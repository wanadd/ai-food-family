export function expiryLabel(days: number, isExpired: boolean): string {
  if (isExpired) {
    return days === -1 ? "Истёк вчера" : `Просрочен на ${Math.abs(days)} дн.`;
  }
  if (days === 0) {
    return "Истекает сегодня";
  }
  if (days === 1) {
    return "Истекает завтра";
  }
  return `Осталось ${days} дн.`;
}

export function expiryTone(
  days: number,
  isExpired: boolean,
): "danger" | "warning" | "ok" {
  if (isExpired) {
    return "danger";
  }
  if (days <= 2) {
    return "warning";
  }
  return "ok";
}

export function defaultExpiryDate(): string {
  const date = new Date();
  date.setDate(date.getDate() + 7);
  return date.toISOString().slice(0, 10);
}
