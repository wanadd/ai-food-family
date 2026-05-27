"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);
import {
  categoryLabel,
  dietLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import type { RecipeDetail, RecipeHistory, RecipeWhy } from "@/lib/recipes/types";
import {
  addRecipeToCollection,
  addRecipeToShopping,
  createRecipeCollection,
  fetchRecipeCollections,
  fetchRecipeHistory,
  fetchRecipeWhy,
  markRecipeCooked,
} from "@/lib/recipes/api";
import type { RecipeCollection } from "@/lib/recipes/types";
import {
  addRecipeToMenu,
  evaluateRecipe,
  fetchRecipeFamilyFit,
  fetchRecipeImproveSuggestions,
} from "@/lib/recipes/analysis-api";
import type {
  RecipeEvaluation,
  RecipeFamilyFit,
  RecipeImproveSuggestion,
} from "@/lib/menu/overview-types";

type RecipeDetailModalProps = {
  recipe: RecipeDetail;
  onClose: () => void;
  onToggleFavorite: () => void;
  togglingFavorite: boolean;
  menuMode?: boolean;
  onAddedToMenu?: () => void;
};

type AiAction = "evaluate" | "improve";

const FIT_STYLES = {
  good: "border-emerald-200 bg-emerald-50 text-emerald-900",
  partial: "border-amber-200 bg-amber-50 text-amber-900",
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

export function RecipeDetailModal({
  recipe,
  onClose,
  onToggleFavorite,
  togglingFavorite,
  menuMode = false,
  onAddedToMenu,
}: RecipeDetailModalProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [evaluation, setEvaluation] = useState<RecipeEvaluation | null>(null);
  const [familyFit, setFamilyFit] = useState<RecipeFamilyFit | null>(null);
  const [suggestions, setSuggestions] = useState<RecipeImproveSuggestion[]>([]);
  const [why, setWhy] = useState<RecipeWhy | null>(null);
  const [whyLoading, setWhyLoading] = useState(true);
  const [history, setHistory] = useState<RecipeHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [markingCooked, setMarkingCooked] = useState(false);
  const [collections, setCollections] = useState<RecipeCollection[]>([]);
  const [collectionId, setCollectionId] = useState<number | null>(null);
  const [collectionName, setCollectionName] = useState("");
  const [collectionVisibility, setCollectionVisibility] = useState<
    "personal" | "family"
  >("personal");
  const [collectionsLoading, setCollectionsLoading] = useState(true);
  const [savingCollection, setSavingCollection] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addingShopping, setAddingShopping] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [aiBusy, setAiBusy] = useState<AiAction | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<AiAction | null>(null);
  const {
    overview: subscription,
    ensureLoaded: ensureSubscriptionLoaded,
    refresh: refreshSubscription,
  } = useSubscriptionOverview();
  const amaBalance = subscription?.ama_balance ?? null;
  const amaCosts = subscription?.ama_costs ?? null;

  /**
   * Auto-load family compatibility only. It is a pure heuristic on the
   * backend (no OpenAI call, no Amas charge) — safe to fetch on mount.
   * AI-backed endpoints /evaluate and /improve are gated behind explicit
   * user clicks and AmaConfirmDialog. Subscription overview is fetched
   * lazily only when user requests an AI action (see requestAiAction).
   */
  const loadFamilyFit = useCallback(async () => {
    if (!initData) return;
    try {
      const fam = await fetchRecipeFamilyFit(initData, mode, recipe.id);
      setFamilyFit(fam);
    } catch {
      setFamilyFit(null);
    }
  }, [initData, mode, recipe.id]);

  const loadWhy = useCallback(async () => {
    if (!initData) {
      setWhyLoading(false);
      return;
    }
    setWhyLoading(true);
    try {
      const result = await fetchRecipeWhy(initData, mode, recipe.id);
      setWhy(result);
    } catch {
      setWhy(null);
    } finally {
      setWhyLoading(false);
    }
  }, [initData, mode, recipe.id]);

  const loadHistory = useCallback(async () => {
    if (!initData) {
      setHistoryLoading(false);
      return;
    }
    setHistoryLoading(true);
    try {
      const result = await fetchRecipeHistory(initData, mode, recipe.id);
      setHistory(result);
    } catch {
      setHistory(null);
    } finally {
      setHistoryLoading(false);
    }
  }, [initData, mode, recipe.id]);

  const loadCollections = useCallback(async () => {
    if (!initData) {
      setCollectionsLoading(false);
      return;
    }
    setCollectionsLoading(true);
    try {
      const result = await fetchRecipeCollections(initData, mode);
      setCollections(result);
      setCollectionId((prev) => prev ?? result[0]?.id ?? null);
    } catch {
      setCollections([]);
      setCollectionId(null);
    } finally {
      setCollectionsLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void loadFamilyFit();
  }, [loadFamilyFit]);

  useEffect(() => {
    void loadWhy();
  }, [loadWhy]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    void loadCollections();
  }, [loadCollections]);

  function requestAiAction(action: AiAction) {
    ensureSubscriptionLoaded();
    setPendingAction(action);
  }

  async function runConfirmedAiAction(action: AiAction) {
    if (!initData) {
      setPendingAction(null);
      return;
    }
    setAiBusy(action);
    setAiError(null);
    try {
      if (action === "evaluate") {
        const ev = await evaluateRecipe(initData, mode, recipe.id);
        setEvaluation(ev);
        void refreshSubscription();
      } else {
        const res = await fetchRecipeImproveSuggestions(
          initData,
          mode,
          recipe.id,
        );
        setSuggestions(res.suggestions ?? []);
      }
    } catch (err) {
      setAiError(
        err instanceof Error
          ? err.message
          : "Не получилось получить ответ AI. Попробуйте ещё раз.",
      );
    } finally {
      setAiBusy(null);
      setPendingAction(null);
    }
  }

  async function handleAddToShopping() {
    if (!initData) return;
    setAddingShopping(true);
    setMessage(null);
    try {
      await addRecipeToShopping(initData, recipe.id, recipe.servings);
      setMessage("Ингредиенты добавлены в список покупок.");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не удалось добавить в покупки",
      );
    } finally {
      setAddingShopping(false);
    }
  }

  async function handleAddToMenu() {
    if (!initData) return;
    setAdding(true);
    setMessage(null);
    try {
      await addRecipeToMenu(initData, mode, recipe.id, {
        meal_type: recipe.meal_type,
      });
      setMessage(
        "Блюдо добавлено в меню. Решение за вами — ПланАм только подсказал.",
      );
      onAddedToMenu?.();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Сначала выберите или создайте меню",
      );
    } finally {
      setAdding(false);
    }
  }

  async function handleMarkCooked() {
    if (!initData) return;
    setMarkingCooked(true);
    setMessage(null);
    try {
      await markRecipeCooked(initData, mode, recipe.id, {
        servings: recipe.servings,
      });
      setMessage("✓ Добавлено в историю");
      await loadHistory();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не получилось добавить в историю",
      );
    } finally {
      setMarkingCooked(false);
    }
  }

  async function handleCreateCollection() {
    if (!initData || !collectionName.trim()) return;
    setSavingCollection(true);
    setMessage(null);
    try {
      const created = await createRecipeCollection(initData, mode, {
        name: collectionName.trim(),
        visibility: collectionVisibility,
      });
      setCollectionName("");
      setCollections((prev) => [...prev, created]);
      setCollectionId(created.id);
      setMessage("Коллекция создана. Можно сохранить в неё рецепт.");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не получилось создать коллекцию",
      );
    } finally {
      setSavingCollection(false);
    }
  }

  async function handleSaveToCollection() {
    if (!initData || collectionId == null) return;
    setSavingCollection(true);
    setMessage(null);
    try {
      await addRecipeToCollection(initData, mode, collectionId, recipe.id);
      setMessage("✓ Рецепт сохранён в коллекцию");
      await loadCollections();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не получилось сохранить рецепт",
      );
    } finally {
      setSavingCollection(false);
    }
  }

  const evaluateCost = amaCosts?.recipe_analyze ?? null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-0 sm:items-center sm:p-4">
      <div
        className="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-modal="true"
      >
        <div className="border-b border-stone-100 px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-stone-900">{recipe.title}</h2>
              <p className="mt-1 text-sm text-stone-500">{recipe.description}</p>
            </div>
            <button
              type="button"
              disabled={togglingFavorite}
              onClick={onToggleFavorite}
              className="text-2xl disabled:opacity-50"
            >
              {recipe.is_favorited ? "★" : "☆"}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="font-semibold text-violet-700">
              {mealLabel(recipe.meal_type)}
            </span>
            <span className="text-stone-400">·</span>
            <span>{categoryLabel(recipe.category)}</span>
            <span className="text-stone-400">·</span>
            <span>{recipe.prep_time_minutes} мин</span>
            {recipe.calories_per_serving ? (
              <>
                <span className="text-stone-400">·</span>
                <span>{Math.round(recipe.calories_per_serving)} ккал</span>
              </>
            ) : null}
            {recipe.protein_g ? (
              <>
                <span className="text-stone-400">·</span>
                <span>Б {Math.round(recipe.protein_g)} г</span>
              </>
            ) : null}
          </div>
          {recipe.is_drink ? (
            <p className="mt-2 text-xs text-stone-500">
              {recipe.is_alcoholic
                ? "Содержит алкоголь — ПланАм рекомендует ограничить при цели «здоровье/спорт»."
                : "Напиток"}
              {recipe.caffeine_mg ? ` · кофеин ~${recipe.caffeine_mg} мг` : ""}
            </p>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 pb-28">
          {aiError ? (
            <p className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              {aiError}
            </p>
          ) : null}

          {evaluation ? (
            <section
              className={`mb-4 rounded-xl border p-3 ${FIT_STYLES[evaluation.fit_level]}`}
            >
              <p className="text-sm font-bold">{evaluation.title}</p>
              <ul className="mt-2 space-y-1 text-xs">
                {evaluation.reasons.map((r) => (
                  <li key={r.code}>· {r.label}</li>
                ))}
              </ul>
              <p className="mt-2 text-[11px] opacity-80">
                Это рекомендация, не запрет — выбор всегда за вами.
              </p>
            </section>
          ) : (
            <section className="mb-4 rounded-xl border border-stone-100 bg-stone-50 p-3">
              <p className="text-sm font-bold text-stone-900">
                AI-оценка рецепта
              </p>
              <p className="mt-1 text-xs text-stone-600">
                ПланАм подскажет, подходит ли блюдо вашей цели и ограничениям.
                Действие платное — Амы спишутся только после подтверждения.
              </p>
              <button
                type="button"
                disabled={aiBusy === "evaluate" || !initData}
                onClick={() => requestAiAction("evaluate")}
                className="mt-3 inline-flex min-h-[40px] items-center rounded-xl bg-stone-900 px-4 text-sm font-semibold text-white disabled:opacity-50"
              >
                {aiBusy === "evaluate" ? "Минуточку…" : "Получить AI-оценку"}
              </button>
            </section>
          )}

          {familyFit && familyFit.members.length > 0 ? (
            <section className="mb-4 rounded-xl border border-stone-100 bg-stone-50 p-3">
              <p className="text-sm font-bold text-stone-900">Совместимость семьи</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {familyFit.members.map((m) => (
                  <li key={m.name} className="flex gap-2">
                    <span>{m.status === "ok" ? "✓" : "⚠"}</span>
                    <span>
                      <span className="font-medium">{m.name}</span>
                      <span className="text-stone-500"> — {m.note}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {suggestions.length > 0 ? (
            <section className="mb-4 rounded-xl border border-violet-100 bg-violet-50/40 p-3">
              <p className="text-sm font-bold text-stone-900">Улучшить рецепт</p>
              <ul className="mt-2 space-y-2 text-xs text-stone-600">
                {suggestions.slice(0, 4).map((s) => (
                  <li key={s.id}>
                    <span className="font-semibold text-stone-800">{s.label}:</span>{" "}
                    {s.description}
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <section className="mb-4 rounded-xl border border-stone-100 bg-stone-50 p-3">
              <p className="text-sm font-bold text-stone-900">
                Как улучшить рецепт
              </p>
              <p className="mt-1 text-xs text-stone-600">
                ПланАм предложит варианты под ваш профиль. Просмотр предложений
                не списывает Амы — Амы списываются только когда вы выберете
                конкретное улучшение и подтвердите его применение.
              </p>
              <button
                type="button"
                disabled={aiBusy === "improve" || !initData}
                onClick={() => requestAiAction("improve")}
                className="mt-3 inline-flex min-h-[40px] items-center rounded-xl border border-stone-200 bg-white px-4 text-sm font-semibold text-stone-800 disabled:opacity-50"
              >
                {aiBusy === "improve" ? "Минуточку…" : "Подобрать улучшения"}
              </button>
            </section>
          )}

          {message ? (
            <p className="mb-3 text-sm text-emerald-800">{message}</p>
          ) : null}

          <section className="mb-4 rounded-xl border border-stone-100 bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-stone-900">Я приготовил</p>
                <p className="mt-1 text-xs text-stone-600">
                  Отметьте блюдо, чтобы ПланАм помнил, что семье уже заходило.
                </p>
              </div>
              <button
                type="button"
                disabled={markingCooked || !initData}
                onClick={() => void handleMarkCooked()}
                className="shrink-0 rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
              >
                {markingCooked ? "…" : "Я приготовил"}
              </button>
            </div>
            <div className="mt-3 rounded-lg bg-stone-50 px-3 py-2 text-xs text-stone-600">
              {historyLoading ? (
                <span>Загружаю историю…</span>
              ) : history?.stats && history.stats.cooked_count > 0 ? (
                <span>
                  Готовили: {history.stats.cooked_count}{" "}
                  {history.stats.cooked_count === 1 ? "раз" : "раза"} · последний раз{" "}
                  {relativeCookedLabel(history.stats.last_cooked_on)}
                </span>
              ) : (
                <span>Пока не готовили. Можно начать историю с одного нажатия.</span>
              )}
            </div>
          </section>

          <section className="mb-4 rounded-xl border border-stone-100 bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-stone-900">
                  Сохранить в коллекцию
                </p>
                <p className="mt-1 text-xs text-stone-600">
                  Избранное — звёздочка сверху. Здесь можно собрать личные и
                  семейные подборки.
                </p>
              </div>
              <span className="text-xl">{recipe.is_favorited ? "★" : "☆"}</span>
            </div>
            {collectionsLoading ? (
              <p className="mt-3 text-xs text-stone-500">Загружаю коллекции…</p>
            ) : collections.length > 0 ? (
              <div className="mt-3 flex gap-2">
                <select
                  value={collectionId ?? ""}
                  onChange={(event) => setCollectionId(Number(event.target.value))}
                  className="min-w-0 flex-1 rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm"
                >
                  {collections.map((collection) => (
                    <option key={collection.id} value={collection.id}>
                      {collection.visibility === "family" ? "Семья · " : "Моя · "}
                      {collection.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={savingCollection || collectionId == null}
                  onClick={() => void handleSaveToCollection()}
                  className="rounded-xl bg-stone-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                >
                  Сохранить
                </button>
              </div>
            ) : (
              <p className="mt-3 text-xs text-stone-500">
                Коллекций пока нет. Создайте первую подборку ниже.
              </p>
            )}
            <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
              <input
                value={collectionName}
                onChange={(event) => setCollectionName(event.target.value)}
                placeholder="Новая коллекция"
                className="rounded-xl border border-stone-200 px-3 py-2 text-sm"
              />
              <select
                value={collectionVisibility}
                onChange={(event) =>
                  setCollectionVisibility(
                    event.target.value === "family" ? "family" : "personal",
                  )
                }
                className="rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm"
              >
                <option value="personal">Личная</option>
                {mode === "family" ? <option value="family">Семейная</option> : null}
              </select>
              <button
                type="button"
                disabled={savingCollection || !collectionName.trim()}
                onClick={() => void handleCreateCollection()}
                className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-900 disabled:opacity-50"
              >
                Создать
              </button>
            </div>
          </section>

          <section className="mb-4 rounded-xl border border-emerald-100 bg-emerald-50/70 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-stone-900">
                  Почему рекомендован
                </p>
                <p className="mt-1 text-xs text-stone-600">
                  Без AI-магии: только понятные факты о рецепте, запасах и семье.
                </p>
              </div>
              <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-emerald-700">
                бесплатно
              </span>
            </div>
            {whyLoading ? (
              <div className="mt-3 space-y-2">
                <div className="h-4 w-4/5 animate-pulse rounded bg-emerald-100" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-emerald-100" />
              </div>
            ) : why && why.positives.length > 0 ? (
              <ul className="mt-3 space-y-1.5 text-sm text-stone-800">
                {why.positives.slice(0, 5).map((reason) => (
                  <li key={reason.code} className="flex gap-2">
                    <span className="text-emerald-600">✓</span>
                    <span>{SIMPLE_REASON_LABELS[reason.code] ?? reason.label}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-stone-600">
                Пока нет особых причин. Рецепт всё равно можно выбрать вручную.
              </p>
            )}
          </section>

          <section>
            <h3 className="text-sm font-bold uppercase tracking-wide text-stone-500">
              Ингредиенты
            </h3>
            <ul className="mt-2 space-y-2">
              {recipe.ingredients.map((item) => (
                <li
                  key={`${item.name}-${item.amount}`}
                  className="flex justify-between gap-2 text-sm"
                >
                  <span className="font-medium text-stone-800">{item.name}</span>
                  <span className="text-stone-500">{item.amount}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-bold uppercase tracking-wide text-stone-500">
              Шаги
            </h3>
            <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm text-stone-700">
              {recipe.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          {recipe.diets.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-1">
              {recipe.diets.map((diet) => (
                <span
                  key={diet}
                  className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800"
                >
                  {dietLabel(diet)}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="border-t border-stone-100 bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <button
            type="button"
            disabled={adding}
            onClick={() => void handleAddToMenu()}
            className="mb-2 w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {adding ? "…" : "Добавить в меню"}
          </button>
          <button
            type="button"
            disabled={addingShopping}
            onClick={() => void handleAddToShopping()}
            className="mb-2 w-full rounded-xl border border-emerald-200 bg-emerald-50 py-3 text-sm font-semibold text-emerald-900 disabled:opacity-50"
          >
            {addingShopping ? "…" : "Добавить в покупки"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-800"
          >
            Закрыть
          </button>
        </div>
      </div>

      <AmaConfirmDialog
        open={pendingAction === "evaluate"}
        title="AI-оценка рецепта"
        description={
          <span>
            ПланАм проверит, подходит ли «{recipe.title}» вашей цели,
            аллергиям и ограничениям. Ответ появится в карточке выше —
            окончательное решение остаётся за вами.
          </span>
        }
        benefit="Поможет понять, насколько рецепт подходит именно вам"
        costAma={evaluateCost}
        balanceAma={amaBalance}
        busy={aiBusy === "evaluate"}
        confirmLabel="Получить AI-оценку"
        onCancel={() => {
          if (aiBusy !== "evaluate") setPendingAction(null);
        }}
        onConfirm={() => void runConfirmedAiAction("evaluate")}
      />

      <AmaConfirmDialog
        open={pendingAction === "improve"}
        title="Подобрать улучшения"
        description={
          <span>
            ПланАм предложит, что можно поменять в рецепте под ваш профиль.
            Просмотр предложений не списывает Амы. Если выберете конкретное
            улучшение и подтвердите его применение — спишется{" "}
            {amaCosts?.recipe_improve != null
              ? `${amaCosts.recipe_improve} Ам/Ама.`
              : "стоимость улучшения (показана в окне подтверждения)."}
          </span>
        }
        benefit="Показать предложения — бесплатно. Применять — выбор за вами"
        costAma={0}
        balanceAma={amaBalance}
        busy={aiBusy === "improve"}
        confirmLabel="Показать предложения"
        onCancel={() => {
          if (aiBusy !== "improve") setPendingAction(null);
        }}
        onConfirm={() => void runConfirmedAiAction("improve")}
      />
    </div>
  );
}
