"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { RecipeDetailMorePanel } from "@/components/recipes/RecipeDetailMorePanel";
import { Sheet } from "@/components/ui/Sheet";
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
  rateRecipeForFamily,
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

function hasNutrition(recipe: RecipeDetail): boolean {
  return [
    recipe.calories_per_serving,
    recipe.protein_g,
    recipe.fat_g,
    recipe.carbs_g,
  ].some((value) => value != null);
}

function nutritionValue(value: number | null | undefined, suffix: string): string {
  return value != null ? `${Math.round(value)} ${suffix}` : "—";
}

export function RecipeDetailModal({
  recipe,
  onClose,
  onToggleFavorite,
  togglingFavorite,
  onAddedToMenu,
}: RecipeDetailModalProps) {
  const { initData } = useTelegram();
  const { mode, context } = useAppMode();
  const [moreOpen, setMoreOpen] = useState(false);
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
  const familyMembers = useMemo(
    () => context?.family?.members ?? [],
    [context?.family?.members],
  );
  const [rateMemberId, setRateMemberId] = useState<number | null>(null);
  const [familyScore, setFamilyScore] = useState(0);
  const [familyVotes, setFamilyVotes] = useState(0);
  const [ratingBusy, setRatingBusy] = useState<"liked" | "loved" | "disliked" | null>(
    null,
  );
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
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const steps = Array.isArray(recipe.steps) ? recipe.steps : [];
  const diets = Array.isArray(recipe.diets) ? recipe.diets : [];

  const loadFamilyFit = useCallback(async () => {
    if (!initData) return;
    try {
      setFamilyFit(await fetchRecipeFamilyFit(initData, mode, recipe.id));
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
      setWhy(await fetchRecipeWhy(initData, mode, recipe.id));
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
      setHistory(await fetchRecipeHistory(initData, mode, recipe.id));
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

  useEffect(() => {
    if (familyMembers.length > 0 && rateMemberId == null) {
      setRateMemberId(familyMembers[0].id);
    }
  }, [familyMembers, rateMemberId]);

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
        setEvaluation(await evaluateRecipe(initData, mode, recipe.id));
        void refreshSubscription();
      } else {
        const res = await fetchRecipeImproveSuggestions(initData, mode, recipe.id);
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
      setMessage("Блюдо добавлено в меню.");
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
      setMessage("Коллекция создана.");
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

  async function handleRateRecipe(rating: "liked" | "loved" | "disliked") {
    if (!initData || rateMemberId == null) return;
    setRatingBusy(rating);
    setMessage(null);
    try {
      await rateRecipeForFamily(initData, mode, recipe.id, {
        family_member_id: rateMemberId,
        rating,
      });
      const delta = rating === "loved" ? 3 : rating === "liked" ? 1 : -2;
      setFamilyScore((prev) => prev + delta);
      setFamilyVotes((prev) => prev + 1);
      setMessage("✓ Оценка семьи сохранена");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не получилось сохранить оценку",
      );
    } finally {
      setRatingBusy(null);
    }
  }

  const evaluateCost = amaCosts?.recipe_analyze ?? null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/50 p-0 sm:items-center sm:p-4">
      <div
        className="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-card bg-cream-surface shadow-lift sm:rounded-card"
        role="dialog"
        aria-modal="true"
      >
        <div className="border-b border-cream-border px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h2 className="text-xl font-bold text-graphite-900">{recipe.title}</h2>
              {recipe.description ? (
                <p className="mt-1 text-sm text-graphite-600">{recipe.description}</p>
              ) : null}
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <button
                type="button"
                disabled={togglingFavorite}
                onClick={onToggleFavorite}
                className="flex h-10 w-10 items-center justify-center rounded-control text-xl disabled:opacity-50"
                aria-label={recipe.is_favorited ? "Убрать из избранного" : "В избранное"}
              >
                {recipe.is_favorited ? "★" : "☆"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex h-10 w-10 items-center justify-center rounded-control text-sm font-semibold text-graphite-500 hover:bg-cream-deep"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-graphite-600">
            <span className="font-semibold text-sage-700">
              {mealLabel(recipe.meal_type)}
            </span>
            <span className="text-graphite-300">·</span>
            <span>{categoryLabel(recipe.category)}</span>
            <span className="text-graphite-300">·</span>
            <span>{recipe.prep_time_minutes} мин</span>
            {recipe.calories_per_serving != null ? (
              <>
                <span className="text-graphite-300">·</span>
                <span>{Math.round(recipe.calories_per_serving)} ккал</span>
              </>
            ) : null}
            {recipe.protein_g != null ? (
              <>
                <span className="text-graphite-300">·</span>
                <span>Б {Math.round(recipe.protein_g)} г</span>
              </>
            ) : null}
          </div>
          {hasNutrition(recipe) ? (
            <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
              <div className="rounded-control bg-cream-deep px-2 py-2">
                <div className="font-semibold text-graphite-900">
                  {nutritionValue(recipe.calories_per_serving, "ккал")}
                </div>
                <div className="mt-0.5 text-graphite-500">Калории</div>
              </div>
              <div className="rounded-control bg-cream-deep px-2 py-2">
                <div className="font-semibold text-graphite-900">
                  {nutritionValue(recipe.protein_g, "г")}
                </div>
                <div className="mt-0.5 text-graphite-500">Белки</div>
              </div>
              <div className="rounded-control bg-cream-deep px-2 py-2">
                <div className="font-semibold text-graphite-900">
                  {nutritionValue(recipe.fat_g, "г")}
                </div>
                <div className="mt-0.5 text-graphite-500">Жиры</div>
              </div>
              <div className="rounded-control bg-cream-deep px-2 py-2">
                <div className="font-semibold text-graphite-900">
                  {nutritionValue(recipe.carbs_g, "г")}
                </div>
                <div className="mt-0.5 text-graphite-500">Углеводы</div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 pb-28">
          {message ? (
            <p className="mb-3 rounded-control border border-sage-200 bg-sage-50 px-3 py-2 text-sm text-sage-900">
              {message}
            </p>
          ) : null}
          {aiError ? (
            <p className="mb-3 rounded-control border border-warm/30 bg-warm/10 px-3 py-2 text-sm text-graphite-900">
              {aiError}
            </p>
          ) : null}

          <section className="pa-card p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-graphite-500">
              Ингредиенты
            </h3>
            <ul className="mt-3 space-y-2">
              {ingredients.map((item) => (
                <li
                  key={`${item.name}-${item.amount}`}
                  className="flex justify-between gap-2 text-sm"
                >
                  <span className="font-medium text-graphite-800">{item.name}</span>
                  <span className="shrink-0 text-graphite-500">{item.amount}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="pa-card mt-3 p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-graphite-500">
              Шаги
            </h3>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-graphite-700">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          {diets.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {diets.map((diet) => (
                <span key={diet} className="pa-chip text-[10px]">
                  {dietLabel(diet)}
                </span>
              ))}
            </div>
          ) : null}

          <button
            type="button"
            onClick={() => setMoreOpen(true)}
            className="pa-btn mt-4 w-full py-3 text-sm"
          >
            Ещё — AI, семья, коллекции…
          </button>
        </div>

        <div className="border-t border-cream-border bg-cream-surface px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <button
            type="button"
            disabled={adding}
            onClick={() => void handleAddToMenu()}
            className="pa-btn-primary mb-2 w-full py-3 text-sm disabled:opacity-50"
          >
            {adding ? "…" : "Добавить в меню"}
          </button>
          <button
            type="button"
            disabled={addingShopping}
            onClick={() => void handleAddToShopping()}
            className="pa-btn w-full py-3 text-sm disabled:opacity-50"
          >
            {addingShopping ? "…" : "Добавить в покупки"}
          </button>
        </div>
      </div>

      <Sheet open={moreOpen} title="Ещё" onClose={() => setMoreOpen(false)}>
        <RecipeDetailMorePanel
          recipe={recipe}
          initData={initData}
          evaluation={evaluation}
          familyFit={familyFit}
          familyMembers={familyMembers}
          rateMemberId={rateMemberId}
          setRateMemberId={setRateMemberId}
          familyScore={familyScore}
          familyVotes={familyVotes}
          ratingBusy={ratingBusy}
          onRate={(r) => void handleRateRecipe(r)}
          suggestions={suggestions}
          aiBusy={aiBusy}
          onRequestAi={requestAiAction}
          why={why}
          whyLoading={whyLoading}
          history={history}
          historyLoading={historyLoading}
          markingCooked={markingCooked}
          onMarkCooked={() => void handleMarkCooked()}
          collections={collections}
          collectionsLoading={collectionsLoading}
          collectionId={collectionId}
          setCollectionId={setCollectionId}
          collectionName={collectionName}
          setCollectionName={setCollectionName}
          collectionVisibility={collectionVisibility}
          setCollectionVisibility={setCollectionVisibility}
          savingCollection={savingCollection}
          onSaveToCollection={() => void handleSaveToCollection()}
          onCreateCollection={() => void handleCreateCollection()}
        />
      </Sheet>

      <AmaConfirmDialog
        open={pendingAction === "evaluate"}
        title="AI-оценка рецепта"
        description={
          <span>
            ПланАм проверит, подходит ли «{recipe.title}» вашей цели и ограничениям.
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
          </span>
        }
        benefit="Просмотр предложений бесплатный"
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
