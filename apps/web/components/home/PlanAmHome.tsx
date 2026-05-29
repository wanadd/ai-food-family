"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { SectionHub } from "@/components/layout/SectionHub";
import { HubTile } from "@/components/ui/HubTile";
import {
  cacheKey,
  fetchOrCache,
  getCached as getCachedOrNull,
} from "@/lib/cache/session-cache";
import { countToBuy, formatGoodsCount } from "@/lib/home/plan-summary";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { SelectedMenu } from "@/lib/menu/types";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

const PREFETCH_TABS = ["/menu", "/shopping", "/health/chat"];

function greetingFor(date: Date): string {
  const h = date.getHours();
  if (h < 6) return "Доброй ночи";
  if (h < 12) return "Доброе утро";
  if (h < 18) return "Добрый день";
  return "Добрый вечер";
}

function truncate(name: string, max = 44): string {
  const t = name.trim();
  return t.length <= max ? t : `${t.slice(0, max - 1)}…`;
}

/** Один главный ответ «что важно сегодня» из активного меню. */
function pickTodayMeal(
  menu: SelectedMenu["menu"] | null,
): { label: string; name: string } | null {
  if (!menu?.meals?.length) return null;
  const dinner = menu.meals.find((m) => m.meal_type === "dinner");
  if (dinner) return { label: "на ужин", name: truncate(dinner.name) };
  const lunch = menu.meals.find((m) => m.meal_type === "lunch");
  if (lunch) return { label: "на обед", name: truncate(lunch.name) };
  return { label: "в плане", name: truncate(menu.meals[0].name) };
}

/**
 * ПланАм Home — навигационный центр на один экран (ONE SCREEN UX).
 *
 * Только: приветствие · один ответ «что важно сегодня» · короткая строка
 * «что купить» · 3 крупные кнопки. Никаких dashboard-блоков, метрик и длинных
 * пояснений. Данные — из session-cache (selected menu + shopping), без новых
 * запросов, AI и изменений API/маршрутов.
 */
export function PlanAmHome() {
  const router = useRouter();
  const { initData, user } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const cachedMenu = initData
    ? getCachedOrNull<SelectedMenu>(cacheKey.selectedMenu(mode))
    : null;
  const cachedShopping = initData
    ? getCachedOrNull<ShoppingList>(cacheKey.shoppingList(mode))
    : null;

  const [loading, setLoading] = useState(
    Boolean(initData) && cachedMenu == null,
  );
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(
    cachedMenu,
  );
  const [shopping, setShopping] = useState<ShoppingList | null>(cachedShopping);
  const [greeting] = useState(() => greetingFor(new Date()));

  useEffect(() => {
    if (modeLoading) {
      setLoading(true);
      return;
    }
    if (!initData) {
      setLoading(false);
      setSelectedMenu(null);
      setShopping(null);
      return;
    }

    let cancelled = false;

    const primed = getCachedOrNull<SelectedMenu>(cacheKey.selectedMenu(mode));
    if (primed != null) {
      setSelectedMenu(primed);
      setLoading(false);
    } else {
      setLoading(true);
    }

    void fetchOrCache(cacheKey.selectedMenu(mode), () =>
      fetchSelectedMenu(initData, mode),
    )
      .then((selected) => {
        if (!cancelled) setSelectedMenu(selected);
      })
      .catch(() => {
        if (!cancelled) setSelectedMenu(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    void fetchOrCache(cacheKey.shoppingList(mode), () =>
      fetchShoppingList(initData, mode),
    )
      .then((list) => {
        if (!cancelled) setShopping(list);
      })
      .catch(() => {
        if (!cancelled) setShopping(null);
      });

    return () => {
      cancelled = true;
    };
  }, [initData, mode, modeLoading]);

  useEffect(() => {
    if (!initData) return;
    for (const path of PREFETCH_TABS) router.prefetch(path);
  }, [initData, router]);

  const firstName = user?.first_name?.trim();
  const title = firstName ? `${greeting}, ${firstName}` : greeting;

  const todayMeal = useMemo(
    () => pickTodayMeal(selectedMenu?.menu ?? null),
    [selectedMenu],
  );
  const toBuy = countToBuy(shopping);
  const buyLine =
    toBuy > 0
      ? `Нужно докупить ${formatGoodsCount(toBuy)}`
      : "Покупки пока пустые";

  const lead = loading ? (
    <div className="pa-card animate-pulse p-4" aria-busy="true">
      <div className="h-3 w-20 rounded bg-cream-deep" />
      <div className="mt-3 h-5 w-3/4 rounded bg-cream-deep" />
    </div>
  ) : (
    <div className="pa-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
        Сегодня
      </p>
      <p className="mt-1.5 text-lg font-bold leading-snug text-graphite-900">
        {todayMeal
          ? `Сегодня ${todayMeal.label}: ${todayMeal.name}`
          : "Давайте составим меню"}
      </p>
    </div>
  );

  return (
    <SectionHub title={title} subtitle="ПланАм" lead={lead}>
      <HubTile
        href="/menu"
        icon="🍽"
        title="Открыть меню"
        hint={todayMeal ? "Ваш план питания" : "Соберите меню за минуту"}
        tone="primary"
      />
      <HubTile href="/shopping" icon="🛒" title="Что купить" hint={buyLine} />
      <HubTile
        href="/health/chat"
        icon="✨"
        title="Спросить ПланАм"
        hint="AI-помощник по питанию"
      />
    </SectionHub>
  );
}
