/** Parse explicit minute durations from Russian step text. */
export function parseStepMinutes(text: string): number | null {
  const match = text.match(/(\d{1,3})\s*(?:мин(?:ут(?:ы|у)?)?|m\b)/i);
  if (!match) {
    return null;
  }
  const minutes = Number(match[1]);
  if (!Number.isFinite(minutes) || minutes <= 0 || minutes > 240) {
    return null;
  }
  return minutes;
}

export function formatTimerLabel(minutes: number): string {
  return `${minutes} мин`;
}
