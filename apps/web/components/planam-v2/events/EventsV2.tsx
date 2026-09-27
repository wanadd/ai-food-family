"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { V2BottomSheet, V2Button, V2Card, V2EmptyState, V2PageHeader } from "@/components/planam-v2/ui/V2Primitives";
import { getErrorMessage } from "@/lib/api-errors";
import { createEvent, listEvents } from "@/lib/events/v2-api";
import type { EventReadModel } from "@/lib/events/v2-types";

function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function statusLabel(status: EventReadModel["status"]): string {
  return { DRAFT: "Черновик", OPEN: "Открыто", PLANNING: "Планируем", READY: "Готово", ACTIVE: "Идёт", COMPLETED: "Завершено", CANCELLED: "Отменено" }[status];
}

export function EventsV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [events, setEvents] = useState<EventReadModel[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error" | "auth">(initData ? "loading" : "auth");
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [eventType, setEventType] = useState("dinner");

  const load = useCallback(async () => {
    if (!initData) { setState("auth"); return; }
    setState("loading"); setError(null);
    try { const result = await listEvents(initData, mode); setEvents(result.items); setState("ready"); }
    catch (err) { setError(getErrorMessage(err)); setState("error"); }
  }, [initData, mode]);

  useEffect(() => { void load(); }, [load]);

  async function submit() {
    if (!initData || !title.trim() || !startsAt) return;
    setBusy(true); setError(null);
    try {
      const event = await createEvent(initData, mode, { title: title.trim(), event_type: eventType, starts_at: new Date(startsAt).toISOString(), collaboration_mode: "RESTRICTIONS_COLLECTION" });
      setCreateOpen(false); setTitle(""); setStartsAt(""); router.push(`/events/${event.event_id}`);
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pb-8 pt-2">
      <V2PageHeader title="События" subtitle="Временные планы для гостей и общих дней" className="px-0" />
      {state === "auth" ? <V2Card><p className="pa26-body">Войдите, чтобы увидеть свои события.</p></V2Card> : null}
      {state === "loading" ? <EventsSkeleton /> : null}
      {state === "error" ? <V2Card><p className="pa26-body text-pa-error">{error}</p><V2Button className="mt-3" variant="secondary" onClick={() => void load()}>Повторить</V2Button></V2Card> : null}
      {state === "ready" && events.length === 0 ? <V2Card><V2EmptyState title="Событий пока нет" description="Создайте отдельный план для гостей, праздника или другого общего дня." actionLabel="Создать событие" onAction={() => setCreateOpen(true)} icon="✦" /></V2Card> : null}
      {state === "ready" && events.length > 0 ? (
        <section className="space-y-3" aria-label="Ваши события">
          <div className="flex items-center justify-between"><p className="pa26-micro text-pa-muted">{events.length} {events.length === 1 ? "событие" : "события"}</p><V2Button size="compact" onClick={() => setCreateOpen(true)}>Новое событие</V2Button></div>
          {events.map((event) => <button key={event.event_id} type="button" onClick={() => router.push(`/events/${event.event_id}`)} className="w-full text-left"><V2Card className="transition hover:border-sage-400 active:scale-[0.99]"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="pa26-card-title truncate">{event.title}</p><p className="pa26-caption mt-1 capitalize">{formatEventDate(event.starts_at)}</p></div><span className="shrink-0 rounded-pill bg-sage-50 px-2 py-1 pa26-micro text-sage-800 dark:bg-sage-900/30 dark:text-sage-300">{statusLabel(event.status)}</span></div><div className="mt-3 flex gap-2 pa26-micro text-pa-muted"><span>Ожидается {event.headcount.expected}</span><span>Подтвердили {event.headcount.confirmed}</span><span>Ограничения {event.food_profile_completeness.known}/{event.food_profile_completeness.accepted}</span></div></V2Card></button>)}
        </section>
      ) : null}
      <V2BottomSheet open={createOpen} title="Новое событие" onClose={() => setCreateOpen(false)} footer={<V2Button size="wide" loading={busy} disabled={!title.trim() || !startsAt} onClick={() => void submit()}>Создать событие</V2Button>}>
        <div className="space-y-4">
          <label className="block"><span className="pa26-micro font-semibold">Название</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например, семейный ужин" className="mt-1 min-h-11 w-full rounded-control border border-pa-border bg-pa-surface px-3 text-pa-foreground outline-none focus:border-sage-500" /></label>
          <label className="block"><span className="pa26-micro font-semibold">Дата и время</span><input type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} className="mt-1 min-h-11 w-full rounded-control border border-pa-border bg-pa-surface px-3 text-pa-foreground outline-none focus:border-sage-500" /></label>
          <label className="block"><span className="pa26-micro font-semibold">Тип события</span><select value={eventType} onChange={(event) => setEventType(event.target.value)} className="mt-1 min-h-11 w-full rounded-control border border-pa-border bg-pa-surface px-3 text-pa-foreground"><option value="dinner">Ужин</option><option value="party">Праздник</option><option value="picnic">Пикник</option><option value="other">Другое</option></select></label>
          {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
        </div>
      </V2BottomSheet>
    </div>
  );
}

function EventsSkeleton() { return <div className="space-y-3" aria-label="Загрузка событий"><div className="h-24 animate-pulse rounded-card bg-pa-elevated" /><div className="h-24 animate-pulse rounded-card bg-pa-elevated" /></div>; }
