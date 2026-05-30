"use client";

import type { ReactNode } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import type {
  RecipeEvaluation,
  RecipeFamilyFit,
  RecipeImproveSuggestion,
} from "@/lib/menu/overview-types";
import type { RecipeCollection, RecipeDetail, RecipeHistory, RecipeWhy } from "@/lib/recipes/types";

const FIT_STYLES = {
  good: "border-sage-200 bg-sage-50 text-graphite-900",
  partial: "border-warm/30 bg-warm/10 text-graphite-900",
  not_recommended: "border-red-200 bg-red-50 text-red-900",
};

const SIMPLE_REASON_LABELS: Record<string, string> = {
  in_pantry: "Часть ингредиентов уже есть дома",
  kids_like: "Нравится детям",
  goal_match: "Подходит вашей цели",
  quick_cooking: "Готовится быстро",
  budget_friendly: "Недорогой рецепт",
  high_protein: "Богат белком",
  low_calorie: "Лёгкий по калориям",
  family_approved: "Семья оценила положительно",
};

function relativeCookedLabel(dateText?: string | null) {
  if (!dateText) return "ещё не готовили";
  const today = new Date();
  const value = new Date(`${dateText}T00:00:00`);
  const days = Math.max(
    0,
    Math.floor((today.getTime() - value.getTime()) / 86_400_000),
  );
  if (days === 0) return "сегодня";
  if (days === 1) return "вчера";
  if (days < 5) return `${days} дня назад`;
  return `${days} дней назад`;
}

type Props = {
  recipe: RecipeDetail;
  initData: string | null;
  evaluation: RecipeEvaluation | null;
  familyFit: RecipeFamilyFit | null;
  familyMembers: { id: number; display_name: string }[];
  rateMemberId: number | null;
  setRateMemberId: (id: number) => void;
  familyScore: number;
  familyVotes: number;
  ratingBusy: "liked" | "loved" | "disliked" | null;
  onRate: (rating: "liked" | "loved" | "disliked") => void;
  suggestions: RecipeImproveSuggestion[];
  aiBusy: "evaluate" | "improve" | null;
  onRequestAi: (action: "evaluate" | "improve") => void;
  why: RecipeWhy | null;
  whyLoading: boolean;
  history: RecipeHistory | null;
  historyLoading: boolean;
  markingCooked: boolean;
  onMarkCooked: () => void;
  collections: RecipeCollection[];
  collectionsLoading: boolean;
  collectionId: number | null;
  setCollectionId: (id: number) => void;
  collectionName: string;
  setCollectionName: (v: string) => void;
  collectionVisibility: "personal" | "family";
  setCollectionVisibility: (v: "personal" | "family") => void;
  savingCollection: boolean;
  onSaveToCollection: () => void;
  onCreateCollection: () => void;
};

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="pa-card p-3">
      <p className="text-sm font-bold text-graphite-900">{title}</p>
      <div className="mt-2">{children}</div>
    </section>
  );
}

export function RecipeDetailMorePanel({
  recipe,
  initData,
  evaluation,
  familyFit,
  familyMembers,
  rateMemberId,
  setRateMemberId,
  familyScore,
  familyVotes,
  ratingBusy,
  onRate,
  suggestions,
  aiBusy,
  onRequestAi,
  why,
  whyLoading,
  history,
  historyLoading,
  markingCooked,
  onMarkCooked,
  collections,
  collectionsLoading,
  collectionId,
  setCollectionId,
  collectionName,
  setCollectionName,
  collectionVisibility,
  setCollectionVisibility,
  savingCollection,
  onSaveToCollection,
  onCreateCollection,
}: Props) {
  const { mode } = useAppMode();

  return (
    <div className="space-y-3 pb-2">
      {evaluation ? (
        <section
          className={`rounded-control border p-3 ${FIT_STYLES[evaluation.fit_level]}`}
        >
          <p className="text-sm font-bold">{evaluation.title}</p>
          <ul className="mt-2 space-y-1 text-xs">
            {evaluation.reasons.map((r) => (
              <li key={r.code}>· {r.label}</li>
            ))}
          </ul>
        </section>
      ) : (
        <Block title="AI-оценка рецепта">
          <p className="text-xs text-graphite-600">
            ПланАм подскажет, подходит ли блюдо вашей цели. Амы спишутся после
            подтверждения.
          </p>
          <button
            type="button"
            disabled={aiBusy === "evaluate" || !initData}
            onClick={() => onRequestAi("evaluate")}
            className="pa-btn-primary mt-3 min-h-[40px] px-4 text-sm disabled:opacity-50"
          >
            {aiBusy === "evaluate" ? "Минуточку…" : "Получить AI-оценку"}
          </button>
        </Block>
      )}

      {familyFit && familyFit.members.length > 0 ? (
        <Block title="Совместимость семьи">
          <ul className="space-y-1.5 text-sm">
            {familyFit.members.map((m) => (
              <li key={m.name} className="flex gap-2">
                <span>{m.status === "ok" ? "✓" : "⚠"}</span>
                <span>
                  <span className="font-medium">{m.name}</span>
                  <span className="text-graphite-500"> — {m.note}</span>
                </span>
              </li>
            ))}
          </ul>
        </Block>
      ) : null}

      {mode === "family" && familyMembers.length > 0 ? (
        <Block title="Нравится семье">
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={rateMemberId ?? ""}
              onChange={(e) => setRateMemberId(Number(e.target.value))}
              className="min-w-[140px] flex-1 rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm"
            >
              {familyMembers.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={ratingBusy !== null}
              onClick={() => onRate("liked")}
              className="pa-btn px-3 py-2 text-sm disabled:opacity-50"
            >
              👍
            </button>
            <button
              type="button"
              disabled={ratingBusy !== null}
              onClick={() => onRate("loved")}
              className="pa-btn px-3 py-2 text-sm disabled:opacity-50"
            >
              ❤️
            </button>
            <button
              type="button"
              disabled={ratingBusy !== null}
              onClick={() => onRate("disliked")}
              className="pa-btn px-3 py-2 text-sm disabled:opacity-50"
            >
              👎
            </button>
          </div>
          <p className="mt-2 text-xs text-graphite-500">
            Оценка семьи: {familyScore > 0 ? "+" : ""}
            {familyScore} · отметок: {familyVotes}
          </p>
        </Block>
      ) : null}

      {suggestions.length > 0 ? (
        <Block title="Улучшить рецепт">
          <ul className="space-y-2 text-xs text-graphite-600">
            {suggestions.slice(0, 4).map((s) => (
              <li key={s.id}>
                <span className="font-semibold text-graphite-800">{s.label}:</span>{" "}
                {s.description}
              </li>
            ))}
          </ul>
        </Block>
      ) : (
        <Block title="Как улучшить рецепт">
          <button
            type="button"
            disabled={aiBusy === "improve" || !initData}
            onClick={() => onRequestAi("improve")}
            className="pa-btn mt-1 w-full py-2.5 text-sm disabled:opacity-50"
          >
            {aiBusy === "improve" ? "Минуточку…" : "Подобрать улучшения"}
          </button>
        </Block>
      )}

      <Block title="Я приготовил">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-graphite-600">
            {historyLoading ? (
              "Загружаю историю…"
            ) : history?.stats && history.stats.cooked_count > 0 ? (
              <>
                Готовили {history.stats.cooked_count} раз · последний раз{" "}
                {relativeCookedLabel(history.stats.last_cooked_on)}
              </>
            ) : (
              "Пока не готовили"
            )}
          </p>
          <button
            type="button"
            disabled={markingCooked || !initData}
            onClick={onMarkCooked}
            className="pa-btn-primary shrink-0 px-3 py-2 text-xs disabled:opacity-50"
          >
            {markingCooked ? "…" : "Отметить"}
          </button>
        </div>
      </Block>

      <Block title="Коллекции">
        {collectionsLoading ? (
          <p className="text-xs text-graphite-500">Загружаю…</p>
        ) : collections.length > 0 ? (
          <div className="flex gap-2">
            <select
              value={collectionId ?? ""}
              onChange={(e) => setCollectionId(Number(e.target.value))}
              className="min-w-0 flex-1 rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm"
            >
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.visibility === "family" ? "Семья · " : "Моя · "}
                  {c.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={savingCollection || collectionId == null}
              onClick={onSaveToCollection}
              className="pa-btn-primary shrink-0 px-3 py-2 text-xs disabled:opacity-50"
            >
              Сохранить
            </button>
          </div>
        ) : (
          <p className="text-xs text-graphite-500">Коллекций пока нет</p>
        )}
        <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
          <input
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
            placeholder="Новая коллекция"
            className="rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm"
          />
          <select
            value={collectionVisibility}
            onChange={(e) =>
              setCollectionVisibility(
                e.target.value === "family" ? "family" : "personal",
              )
            }
            className="rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm"
          >
            <option value="personal">Личная</option>
            {mode === "family" ? <option value="family">Семейная</option> : null}
          </select>
          <button
            type="button"
            disabled={savingCollection || !collectionName.trim()}
            onClick={onCreateCollection}
            className="pa-btn px-3 py-2 text-xs disabled:opacity-50"
          >
            Создать
          </button>
        </div>
      </Block>

      <Block title="Почему рекомендован">
        {whyLoading ? (
          <p className="text-xs text-graphite-500">Загружаю…</p>
        ) : why && why.positives.length > 0 ? (
          <ul className="space-y-1.5 text-sm text-graphite-800">
            {why.positives.slice(0, 5).map((reason) => (
              <li key={reason.code} className="flex gap-2">
                <span className="text-sage-600">✓</span>
                <span>{SIMPLE_REASON_LABELS[reason.code] ?? reason.label}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-graphite-600">
            Пока нет особых причин — рецепт можно выбрать вручную.
          </p>
        )}
      </Block>
    </div>
  );
}
