export type CalendarEventInput = {
  title: string;
  description?: string;
  start: Date;
  durationMinutes?: number;
};

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function formatIcsUtc(date: Date): string {
  return (
    `${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}` +
    `T${pad(date.getUTCHours())}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}Z`
  );
}

export function buildIcsFile(events: CalendarEventInput[]): string {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//PlanAm//RU",
    "CALSCALE:GREGORIAN",
  ];
  for (const ev of events) {
    const end = new Date(ev.start.getTime() + (ev.durationMinutes ?? 30) * 60_000);
    lines.push(
      "BEGIN:VEVENT",
      `DTSTART:${formatIcsUtc(ev.start)}`,
      `DTEND:${formatIcsUtc(end)}`,
      `SUMMARY:${ev.title.replace(/\n/g, " ")}`,
      ev.description ? `DESCRIPTION:${ev.description.replace(/\n/g, " ")}` : "",
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  return lines.filter(Boolean).join("\r\n");
}

export function downloadIcs(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function nextOccurrence(timeHHMM: string, weekdayIndex: number): Date {
  const [h, m] = timeHHMM.split(":").map(Number);
  const now = new Date();
  const d = new Date(now);
  d.setHours(h ?? 9, m ?? 0, 0, 0);
  const diff = (weekdayIndex - d.getDay() + 7) % 7;
  if (diff === 0 && d <= now) {
    d.setDate(d.getDate() + 7);
  } else {
    d.setDate(d.getDate() + diff);
  }
  return d;
}
