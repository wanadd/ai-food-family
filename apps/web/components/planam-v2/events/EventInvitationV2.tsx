"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { V2Button, V2Card } from "@/components/planam-v2/ui/V2Primitives";
import { getErrorMessage } from "@/lib/api-errors";
import { inspectEventInvitation, respondEventInvitation } from "@/lib/events/v2-api";

export function EventInvitationV2() {
  const params = useSearchParams(); const token = params.get("token") ?? "";
  const [invite, setInvite] = useState<{ title: string; starts_at: string; status: string } | null>(null); const [name, setName] = useState(""); const [state, setState] = useState<"loading" | "ready" | "error" | "sent">("loading"); const [error, setError] = useState<string | null>(null); const [food, setFood] = useState("UNKNOWN"); const [busy, setBusy] = useState(false);
  useEffect(() => { if (!token) { setState("error"); setError("В ссылке нет приглашения"); return; } void inspectEventInvitation(token).then((value) => { setInvite(value); setState("ready"); }).catch((err) => { setState("error"); setError(getErrorMessage(err)); }); }, [token]);
  async function submit() { if (!name.trim()) return; setBusy(true); setError(null); try { await respondEventInvitation(token, [{ display_name: name.trim(), age_group: "ADULT", knowledge_state: food, restrictions: [] }]); setState("sent"); } catch (err) { setError(getErrorMessage(err)); } finally { setBusy(false); } }
  if (state === "loading") return <div className="mx-auto max-w-md px-4 pt-8"><V2Card><p className="pa26-body text-pa-muted">Проверяем приглашение…</p></V2Card></div>;
  if (state === "error") return <div className="mx-auto max-w-md px-4 pt-8"><V2Card><h1 className="pa26-page-title">Приглашение недоступно</h1><p className="pa26-body mt-2 text-pa-error">{error}</p></V2Card></div>;
  if (state === "sent") return <div className="mx-auto max-w-md px-4 pt-8"><V2Card><h1 className="pa26-page-title">Ответ отправлен</h1><p className="pa26-body mt-2 text-pa-muted">Организатор увидит ваше участие и ответ по ограничениям.</p></V2Card></div>;
  return <div className="mx-auto max-w-md space-y-4 px-4 pb-8 pt-8"><header><p className="pa26-micro text-pa-muted">Приглашение в PLANAM</p><h1 className="pa26-page-title mt-1">{invite?.title}</h1><p className="pa26-body mt-2 text-pa-muted">{invite ? new Intl.DateTimeFormat("ru-RU", { dateStyle: "full", timeStyle: "short" }).format(new Date(invite.starts_at)) : ""}</p></header><V2Card><h2 className="pa26-section-title">Ваш ответ</h2><label className="mt-4 block"><span className="pa26-micro font-semibold">Как вас зовут?</span><input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 min-h-11 w-full rounded-control border border-pa-border bg-pa-surface px-3" /></label><label className="mt-4 block"><span className="pa26-micro font-semibold">Ограничения по еде</span><select value={food} onChange={(event) => setFood(event.target.value)} className="mt-1 min-h-11 w-full rounded-control border border-pa-border bg-pa-surface px-3"><option value="UNKNOWN">Пока не знаю / не отвечать</option><option value="KNOWN_NONE">Ограничений нет</option><option value="KNOWN_PRESENT">Есть ограничения</option></select></label><V2Button size="wide" className="mt-5" loading={busy} disabled={!name.trim()} onClick={() => void submit()}>Подтвердить участие</V2Button>{error ? <p className="pa26-caption mt-2 text-pa-error">{error}</p> : null}</V2Card></div>;
}
