"use client";

/**
 * PLANAM V2 — Соберём меню (/plan/generate).
 * Один экран настроек (дни, цель, запасы, семья) → staged AI loading →
 * выбор варианта → «Меню готово» с действиями.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiProcessLoadingV2 } from "@/components/planam-v2/ai/AiProcessLoadingV2";
import {
  V2Button,
  V2Card,
  V2Chip,
  V2EmptyState,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { ApiRequestError } from "@/lib/api-errors";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import {
  DEFAULT_MENU_DURATION_DAYS,
  MENU_DURATION_OPTIONS,
  formatMenuDuration,
  menuDurationChipLabel,
  type MenuDurationDays,
} from "@/lib/menu/duration-options";
import { generateMenus, selectMenu } from "@/lib/menu/api";
import { VARIANT_LABELS } from "@/lib/menu/labels";
import {
  MENU_GOAL_OPTIONS,
  type MenuGoalId,
} from "@/lib/menu/planner-options";
import type { MenuVariant } from "@/lib/menu/types";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import { fetchPantry } from "@/lib/pantry/api";
import { cn } from "@/lib/planam/cn";
import { PLANAM_ROUTES } from "@/lib/planam/routes";

type Step = "settings" | "generating" | "choose" | "done" | "error";

export function GenerateMenuV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [step, setStep] = useState<Step>("settings");
  const [planDays, setPlanDays] = useState<MenuDurationDays>(DEFAULT_MENU_DURATION_DAYS);
  const [goal, setGoal] = useState<MenuGoalId | null>(null);
  const [usePantry, setUsePantry] = useState(true);
  const [useFamily, setUseFamily] = useState(true);
  const [pantryCount, setPantryCount] = useState(0);
  const [pantryList, setPantryList] = useState<
    Awaited<ReturnType<typeof fetchPantry>> | null
  >(null);
  const [variants, setVariants] = useState<MenuVariant[]>([]);
  const [genError, setGenError] = useState<string | null>(null);
  const [selecting, setSelecting] = useState(false);

  const familyAvailable = mode === "family" && Boolean(context?.family);

  const personsCount = useMemo(() => {
    if (familyAvailable && useFamily && context?.family) {
      return context.family.members_count ?? context.family.members.length ?? 1;
    }
    return 1;
  }, [familyAvailable, useFamily, context]);

  useEffect(() => {
    if (!initData || modeLoading) {
      return;
    }
    void (async () => {
      const [profile, pantry] = await Promise.all([
        fetchNutritionProfile(initData).catch(() => null),
        fetchPantry(initData, mode).catch(() => null),
      ]);
      const ng = profile?.nutrition_goal as MenuGoalId | undefined;
      if (ng && MENU_GOAL_OPTIONS.some((o) => o.value === ng)) {
        setGoal(ng);
      }
      setPantryList(pantry);
      setPantryCount(pantry?.active_count ?? 0);
    })();
  }, [initData, mode, modeLoading]);

  const runGenerate = useCallback(async () => {
    if (!initData || !goal) {
      return;
    }
    const genMode = familyAvailable && useFamily ? "family" : "personal";
    setStep("generating");
    setGenError(null);
    try {
      const result = await generateMenus(initData, genMode, {
        mode: genMode,
        goal,
        personsCount,
        planDays,
        planMode: usePantry ? "use_pantry" : "healthy",
        wizardBudget: "standard",
        pantry: usePantry ? pantryList : null,
      });
      setVariants(result.menus ?? []);
      setStep("choose");
    } catch (err) {
      setStep("error");
      setGenError(
        err instanceof ApiRequestError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Не удалось создать меню",
      );
    }
  }, [
    initData,
    goal,
    familyAvailable,
    useFamily,
    personsCount,
    planDays,
    usePantry,
    pantryList,
  ]);

  async function handleSelect(menu: MenuVariant) {
    if (!initData) {
      return;
    }
    setSelecting(true);
    try {
      const genMode = familyAvailable && useFamily ? "family" : "personal";
      await selectMenu(initData, genMode, menu);
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      setStep("done");
    } catch (err) {
      setGenError(
        err instanceof Error ? err.message : "Не удалось сохранить план",
      );
    } finally {
      setSelecting(false);
    }
  }

  if (step === "generating") {
    return (
      <div className="px-4 pb-8 pt-4">
        <AiProcessLoadingV2
          variant="menu"
          title={`Собираем меню на ${formatMenuDuration(planDays)}`}
          subtitle="Подбираем блюда под цель, ограничения и запасы"
        />
      </div>
    );
  }

  if (step === "error") {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>🤖</span>}
          title="Не получилось собрать меню"
          description={genError ?? "Попробуйте ещё раз."}
          actionLabel="Повторить"
          onAction={() => void runGenerate()}
        />
      </div>
    );
  }

  if (step === "done") {
    return (
      <div className="space-y-4 px-4 pb-8 pt-8">
        <div className="text-center">
          <span className="text-4xl" aria-hidden>
            ✅
          </span>
          <h1 className="pa26-page-title mt-3">Меню готово</h1>
          <p className="pa26-body mt-1 text-pa-muted">
            План на {formatMenuDuration(planDays)} сохранён. Список покупок
            обновился автоматически.
          </p>
        </div>
        <V2Button
          variant="primary"
          size="wide"
          onClick={() => router.push(`${PLANAM_ROUTES.planToday}?saved=1`)}
        >
          Открыть меню
        </V2Button>
        <V2Button
          variant="secondary"
          size="wide"
          onClick={() => router.push(PLANAM_ROUTES.shopping)}
        >
          Посмотреть покупки
        </V2Button>
        <V2Button
          variant="ghost"
          size="wide"
          onClick={() => {
            setVariants([]);
            setStep("settings");
          }}
        >
          Пересобрать
        </V2Button>
      </div>
    );
  }

  if (step === "choose") {
    return (
      <div className="space-y-3 px-4 pb-8 pt-4">
        <header>
          <h1 className="pa26-page-title">Выберите план</h1>
          <p className="pa26-micro mt-0.5 text-pa-muted">
            Один вариант станет активным, покупки обновятся автоматически
          </p>
        </header>
        {genError ? (
          <p className="rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
            {genError}
          </p>
        ) : null}
        {variants.length === 0 ? (
          <V2EmptyState
            title="Вариантов нет"
            description="Попробуйте пересобрать меню."
            actionLabel="Повторить"
            onAction={() => void runGenerate()}
          />
        ) : (
          variants.map((menu) => {
            const meta = VARIANT_LABELS[menu.variant];
            return (
              <V2Card key={menu.variant}>
                <p className="pa26-card-title">
                  {meta.emoji} {menu.title}
                </p>
                <p className="pa26-caption mt-1 text-pa-muted">{menu.tagline}</p>
                <V2Button
                  variant="primary"
                  className="mt-3 w-full"
                  loading={selecting}
                  onClick={() => void handleSelect(menu)}
                >
                  Выбрать
                </V2Button>
              </V2Card>
            );
          })
        )}
        <V2Button variant="ghost" size="wide" onClick={() => void runGenerate()}>
          Пересобрать
        </V2Button>
      </div>
    );
  }

  return (
    <div className="space-y-4 px-4 pb-8 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <header>
        <h1 className="pa26-page-title">Соберём меню</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          PLANAM подберёт блюда и сразу подготовит покупки
        </p>
      </header>

      <section>
        <h2 className="pa26-section-title">На сколько дней собрать меню?</h2>
        <div className="mt-2 flex gap-2">
          {MENU_DURATION_OPTIONS.map((d) => (
            <V2Chip
              key={d}
              label={menuDurationChipLabel(d)}
              active={planDays === d}
              onClick={() => setPlanDays(d)}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="pa26-section-title">Цель</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {MENU_GOAL_OPTIONS.map((o) => (
            <V2Chip
              key={o.value}
              label={o.label}
              active={goal === o.value}
              onClick={() => setGoal(o.value)}
            />
          ))}
        </div>
      </section>

      <SwitchRow
        title="Учитывать продукты дома"
        hint={
          usePantry
            ? `Сначала используем запасы (${pantryCount} прод.)`
            : "Меню без учёта запасов"
        }
        checked={usePantry}
        onChange={setUsePantry}
      />

      {familyAvailable ? (
        <SwitchRow
          title="Учитывать семью"
          hint={
            useFamily
              ? "Учитываем членов семьи и их ограничения"
              : "План только для вас"
          }
          checked={useFamily}
          onChange={setUseFamily}
        />
      ) : null}

      <V2Button
        variant="primary"
        size="wide"
        disabled={!goal}
        onClick={() => void runGenerate()}
      >
        Собрать меню на {formatMenuDuration(planDays)}
      </V2Button>
      {!goal ? (
        <p className="pa26-micro text-center text-pa-muted">
          Выберите цель — и можно собирать
        </p>
      ) : null}
    </div>
  );
}

function SwitchRow({
  title,
  hint,
  checked,
  onChange,
}: {
  title: string;
  hint: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between gap-3 rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left"
    >
      <span className="min-w-0">
        <span className="pa26-card-title block">{title}</span>
        <span className="pa26-micro mt-0.5 block text-pa-muted">{hint}</span>
      </span>
      <span
        aria-hidden
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-pill transition-colors",
          checked ? "bg-sage-500 dark:bg-sage-400" : "bg-pa-border",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow-soft transition-all",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </span>
    </button>
  );
}
