"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { MenuSlotSheet2026 } from "@/components/recipes-2026/MenuSlotSheet2026";
import { MealEatenSheetV2 } from "@/components/planam-v2/menu/MealEatenSheetV2";
import { ReplaceDishSheet2026 } from "@/components/plan-2026/ReplaceDishSheet2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { fetchSelectedMenu, replaceMenuSlot } from "@/lib/menu/api";
import {
  buildReplaceCatalogUrl,
  parseCurrentRecipeId,
  parseReplaceSlot,
} from "@/lib/menu/replace-slot";
import { readReturnTo } from "@/lib/navigation/return-to";
import { defaultDayIndex } from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  addRecipeToShopping,
  fetchRecipe,
  markRecipeCooked,
  toggleRecipeFavorite,
} from "@/lib/recipes/api";
import {
  categoryLabel,
  difficultyLabel,
  dietLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import { recipeDetailHeading } from "@/lib/recipes/card-title";
import {
  confidenceNote,
  perServingMacros,
  totalMacrosLine,
} from "@/lib/recipes/nutrition";
import { formatIngredientAmount } from "@/lib/recipes/ingredient-amount";
import type { RecipeDetail } from "@/lib/recipes/types";
type RecipeDetail2026Props = {
  recipeId: number;
};

function RecipeDescription({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const needsToggle = text.length > 140 || text.split(/\s+/).length > 24;

  return (
    <div className="mt-2">
      <p
        className={`pa26-body text-pa-muted ${expanded ? "" : "line-clamp-3"}`}
      >
        {text}
      </p>
      {needsToggle ? (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 pa26-micro font-semibold text-sage-600 dark:text-sage-300"
        >
          {expanded ? "Свернуть" : "Показать полностью"}
        </button>
      ) : null}
    </div>
  );
}

function nutritionMetrics(recipe: RecipeDetail): Array<{ label: string; value: string }> {
  const summary = recipe.nutrition_summary;
  const approx = summary?.confidence === "low_confidence" ? "≈" : "";
  const kcal = summary?.kcal_per_serving ?? recipe.calories_per_serving;
  const protein = summary?.protein_per_serving ?? recipe.protein_g;
  const fat = summary?.fat_per_serving ?? recipe.fat_g;
  const carbs = summary?.carbs_per_serving ?? recipe.carbs_g;
  return [
    { label: "Калории", value: kcal != null ? `${approx}${Math.round(kcal)} ккал` : "—" },
    { label: "Белки", value: protein != null ? `${approx}${Math.round(protein)} г` : "—" },
    { label: "Жиры", value: fat != null ? `${approx}${Math.round(fat)} г` : "—" },
    { label: "Углеводы", value: carbs != null ? `${approx}${Math.round(carbs)} г` : "—" },
  ];
}

function NutritionBlock({ recipe }: { recipe: RecipeDetail }) {
  const summary = recipe.nutrition_summary;
  if (!summary || !summary.confidence) {
    return null;
  }
  const note = confidenceNote(summary.confidence);
  if (summary.confidence === "unavailable") {
    return (
      <section className="mt-6">
        <h2 className="pa26-section-title mb-3">КБЖУ на порцию</h2>
        <Card2026 padding="md">
          <p className="pa26-body text-pa-muted">{note}</p>
        </Card2026>
      </section>
    );
  }
  const macros = perServingMacros(summary);
  const totalLine = totalMacrosLine(summary);
  const approximate = summary.confidence === "low_confidence";
  return (
    <section className="mt-6">
      <h2 className="pa26-section-title mb-3">
        КБЖУ на порцию
        {approximate ? (
          <span className="ml-2 pa26-micro font-normal text-pa-muted">
            примерно
          </span>
        ) : null}
      </h2>
      <Card2026 padding="none">
        <div className="grid grid-cols-4 divide-x divide-pa-border">
          {macros.map((m) => (
            <div key={m.label} className="px-2 py-3 text-center">
              <p className="pa26-caption font-semibold text-pa-foreground">
                {approximate && m.value !== "—" ? `≈${m.value}` : m.value}
              </p>
              <p className="pa26-micro mt-0.5 text-pa-muted">{m.label}</p>
            </div>
          ))}
        </div>
        {totalLine ? (
          <div className="border-t border-pa-border px-4 py-2 pa26-micro text-pa-muted">
            На весь рецепт: {totalLine}
          </div>
        ) : null}
      </Card2026>
      {note ? (
        <p className="mt-2 pa26-micro text-pa-muted">{note}</p>
      ) : null}
    </section>
  );
}

export function RecipeDetail2026({ recipeId }: RecipeDetail2026Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const replaceSlot = parseReplaceSlot(searchParams.get("replaceSlot"));
  const replaceMode = replaceSlot != null;
  const returnTo = readReturnTo(
    searchParams,
    replaceSlot ? "/plan/recipes" : "/plan/recipes",
  );
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [shoppingBusy, setShoppingBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [replaceOpen, setReplaceOpen] = useState(false);
  const [replaceBusy, setReplaceBusy] = useState(false);
  const [cookedOpen, setCookedOpen] = useState(false);
  const [cookingStarted, setCookingStarted] = useState(false);
  const [cookedSaved, setCookedSaved] = useState(false);
  const [cookingBusy, setCookingBusy] = useState(false);

  const load = useCallback(async () => {
    if (!initData || !recipeId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipe(initData, recipeId);
      setRecipe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Рецепт не найден");
    } finally {
      setLoading(false);
    }
  }, [initData, recipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!initData || !replaceOpen) {
      return;
    }
    void fetchSelectedMenu(initData, mode).then((s) => setMenu(s?.menu ?? null));
  }, [initData, mode, replaceOpen]);

  async function handleAddShopping() {
    if (!initData || !recipe) {
      return;
    }
    setShoppingBusy(true);
    try {
      await addRecipeToShopping(initData, recipe.id, undefined, mode);
      invalidateCache("shopping-list");
      invalidateCache("menu-overview");
      showToast("Ингредиенты добавлены в список покупок");
    } catch {
      showToast("Не удалось добавить ингредиенты. Попробуйте ещё раз.");
    } finally {
      setShoppingBusy(false);
    }
  }

  async function handleReplaceSlot() {
    if (!initData || !replaceSlot || !recipe) {
      showToast("Не удалось заменить блюдо");
      return;
    }
    setReplaceBusy(true);
    try {
      await replaceMenuSlot(
        initData,
        mode,
        replaceSlot,
        recipe.id,
        recipe.servings ?? 2,
      );
      showToast("Блюдо заменено");
      router.push(readReturnTo(searchParams, "/plan/today"));
    } catch {
      showToast("Не удалось заменить блюдо");
    } finally {
      setReplaceBusy(false);
    }
  }

  async function handleFavorite() {
    if (!initData || !recipe) return;
    setToggling(true);
    try {
      const result = await toggleRecipeFavorite(initData, recipe.id);
      setRecipe({ ...recipe, is_favorited: result.is_favorited });
    } finally {
      setToggling(false);
    }
  }

  async function handleCooked() {
    if (!initData || !recipe) return;
    setCookingBusy(true);
    try {
      await markRecipeCooked(initData, mode, recipe.id, {
        servings: recipe.servings ?? 1,
      });
      setCookedSaved(true);
      showToast("Приготовлено — это ещё не считается съеденным");
    } catch {
      setCookedSaved(true);
      showToast("Приготовлено. Отметку питания можно добавить отдельно.");
    } finally {
      setCookingBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="pb-8">
        <Skeleton2026 variant="rect" aspectRatio="16/9" className="max-h-[40vh] rounded-none" />
        <div className="space-y-3 px-4 pt-4">
          <Skeleton2026 variant="text" className="max-w-[80%]" />
          <Skeleton2026 variant="text" />
          <Skeleton2026 variant="rect" className="h-24" />
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="px-4 py-12">
        <EmptyState2026
          title="Рецепт недоступен"
          description={error ?? "Попробуйте вернуться в каталог."}
          actionLabel="К рецептам"
          onAction={() => router.push("/plan/recipes")}
        />
      </div>
    );
  }

  const heading = recipeDetailHeading(recipe);
  const prep = recipe.prep_time_minutes ?? recipe.cooking_time_minutes ?? 30;
  const meal = mealLabel(recipe.meal_type);
  const category = categoryLabel(recipe.category);
  const diets = Array.isArray(recipe.diets) ? recipe.diets : [];
  const nutrition = nutritionMetrics(recipe);
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const steps = Array.isArray(recipe.steps) ? recipe.steps : [];

  return (
    <div className="pb-4">
      <div className="relative max-h-[40vh]">
        <RecipeImage2026
          imageSource={recipe}
          alt={heading}
          variant="hero"
          mealType={recipe.meal_type}
          className="max-h-[40vh] rounded-none"
          priority
        />
        <Link
          href={
            replaceSlot
              ? buildReplaceCatalogUrl(
                  replaceSlot,
                  parseCurrentRecipeId(searchParams.get("currentRecipeId")),
                  returnTo,
                )
              : returnTo
          }
          className="absolute left-4 top-[max(0.75rem,env(safe-area-inset-top))] rounded-control bg-pa-surface/90 px-3 py-1.5 pa26-micro font-semibold shadow-soft backdrop-blur-sm"
        >
          ← Каталог
        </Link>
      </div>

      <div className="px-4 pt-4">
        <h1 className="pa26-hero leading-tight">{heading}</h1>
        {recipe.description ? (
          <RecipeDescription text={recipe.description} />
        ) : null}

        <div className="mt-4 grid grid-cols-4 gap-2">
          {nutrition.map((metric) => (
            <MetricChip key={metric.label} label={metric.label} value={metric.value} />
          ))}
        </div>

        <div className="mt-2 grid grid-cols-3 gap-2">
          <MetricChip label="Время" value={`${prep} мин`} />
          <MetricChip label="Сложность" value={difficultyLabel(recipe.difficulty)} />
          {meal ? <MetricChip label="Приём" value={meal} /> : null}
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {category ? (
            <span className="rounded-pill bg-sage-50 px-2.5 py-1 pa26-micro font-semibold text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
              {category}
            </span>
          ) : null}
          {diets.slice(0, 3).map((d) => (
            <span
              key={d}
              className="rounded-pill bg-cream-deep px-2.5 py-1 pa26-micro text-pa-muted dark:bg-graphite-700/40"
            >
              {dietLabel(d)}
            </span>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {replaceMode ? (
            <Button2026
              variant="primary"
              className="flex-1 min-w-[120px]"
              loading={replaceBusy}
              onClick={() => void handleReplaceSlot()}
            >
              Заменить блюдо
            </Button2026>
          ) : (
            <>
              <Button2026
                variant="primary"
                className="w-full"
                onClick={() => {
                  setCookingStarted(true);
                  document
                    .getElementById("recipe-cooking-steps")
                    ?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
              >
                Начать готовить
              </Button2026>
              <Button2026
                variant="secondary"
                className="flex-1 min-w-[120px]"
                onClick={() => {
                  if (!initData) {
                    void showToast("Добавление в меню доступно в Telegram Mini App");
                    return;
                  }
                  setAddOpen(true);
                }}
              >
                В меню
              </Button2026>
              <Button2026 variant="secondary" onClick={() => setReplaceOpen(true)}>
                Заменить
              </Button2026>
            </>
          )}
          <Button2026
            variant="ghost"
            loading={shoppingBusy}
            onClick={() => void handleAddShopping()}
          >
            В покупки
          </Button2026>
          <Button2026
            variant="ghost"
            onClick={() => void handleFavorite()}
            loading={toggling}
          >
            {recipe.is_favorited ? "★" : "☆"}
          </Button2026>
        </div>

        <NutritionBlock recipe={recipe} />

        <section className="mt-6">
          <h2 className="pa26-section-title mb-3">Ингредиенты</h2>
          <Card2026 padding="none">
            <ul className="divide-y divide-pa-border">
              {ingredients.map((ing, i) => (
                <li key={`${ing.name}-${i}`} className="flex justify-between gap-3 px-4 py-3 pa26-body">
                  <span>{ing.name}</span>
                  <span className="shrink-0 text-pa-muted">
                    {formatIngredientAmount(ing)}
                  </span>
                </li>
              ))}
            </ul>
          </Card2026>
        </section>

        <section id="recipe-cooking-steps" className="mt-6 scroll-mt-4">
          <h2 className="pa26-section-title mb-3">Приготовление</h2>
          {steps.length === 0 ? (
            <Card2026 padding="md">
              <p className="pa26-body text-pa-muted">
                Пошаговые инструкции появятся, когда рецепт будет дополнен.
              </p>
            </Card2026>
          ) : (
            <ol className="space-y-2">
              {steps.map((step, index) => (
                <li
                  key={index}
                  className="flex gap-3 rounded-card border border-pa-border bg-pa-surface p-3.5"
                >
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-sage-500 text-sm font-bold text-white dark:bg-sage-400">
                    {index + 1}
                  </span>
                  <p className="pa26-body flex-1 leading-snug">{step}</p>
                </li>
              ))}
            </ol>
          )}
          {!replaceMode ? (
            <div className="mt-4 space-y-2">
              {cookingStarted ? (
                <p className="rounded-card border border-sage-200 bg-sage-50 px-3 py-2 pa26-caption text-sage-800 dark:border-sage-700/40 dark:bg-sage-700/20 dark:text-sage-300">
                  Режим готовки открыт. Следуйте шагам и отметьте блюдо готовым, когда закончите.
                </p>
              ) : null}
              <Button2026
                variant="primary"
                size="wide"
                loading={cookingBusy}
                onClick={() => void handleCooked()}
              >
                Приготовлено
              </Button2026>
              {cookedSaved ? (
                <Button2026
                  variant="secondary"
                  size="wide"
                  onClick={() => setCookedOpen(true)}
                >
                  Отметить, кто съел
                </Button2026>
              ) : null}
            </div>
          ) : null}
        </section>
      </div>

      {!replaceMode ? (
        <>
          <MenuSlotSheet2026
            open={addOpen}
            recipe={recipe}
            mode="add"
            onClose={() => setAddOpen(false)}
            onSuccess={() => {
              showToast("Рецепт добавлен в меню");
              router.push("/plan/today?saved=1");
            }}
            onError={() => {
              showToast("Не удалось добавить рецепт в меню. Попробуйте ещё раз.");
            }}
          />
          <ReplaceDishSheet2026
            open={replaceOpen}
            menu={menu}
            dayIndex={menu ? defaultDayIndex(menu) : 1}
            onClose={() => setReplaceOpen(false)}
            onSuccess={() => router.push("/plan/today")}
          />
          <MealEatenSheetV2
            open={cookedOpen}
            onClose={() => setCookedOpen(false)}
            mealType={
              ["breakfast", "lunch", "dinner", "snack"].includes(
                recipe.meal_type ?? "",
              )
                ? recipe.meal_type
                : null
            }
            mealName={heading}
            recipeId={recipe.id}
          />
        </>
      ) : null}
    </div>
  );
}

function MetricChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-card border border-pa-border bg-pa-surface px-3 py-2.5 shadow-soft dark:shadow-none">
      <p className="pa26-micro text-pa-muted">{label}</p>
      <p className="pa26-caption mt-0.5 font-medium text-pa-foreground">{value}</p>
    </div>
  );
}
