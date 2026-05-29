"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ProtectedScreenFallback } from "@/components/auth/ProtectedScreenFallback";
import { SectionHub } from "@/components/layout/SectionHub";
import { HubTile } from "@/components/ui/HubTile";
import { cacheKey, getCached } from "@/lib/cache/session-cache";
import type { MenuVariant } from "@/lib/menu/types";
import { withReturnTo } from "@/lib/navigation/return-to";
import { pickMainAdvice } from "@/lib/nutritionist/main-advice";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { PantryList } from "@/lib/pantry/types";
import { useProtectedScreen } from "@/lib/use-protected-screen";

const HEALTH_RETURN = "/health";

/**
 * Раздел «Здоровье» — лёгкий навигационный хаб (ONE SCREEN UX).
 *
 * Вместо длинного dashboard — один экран: короткий главный ответ
 * («что важно сейчас») + 4 крупные кнопки-дерева: Сегодня · Цели · Прогресс ·
 * AI-рекомендации. Хаб НЕ делает сетевых запросов — совет берётся из уже
 * закэшированных данных (session-cache), тяжёлое содержимое живёт в подэкранах.
 */
export function NutritionistDashboard() {
  const { initData, state: authState } = useProtectedScreen();
  const { mode } = useAppMode();

  if (authState !== "ready") {
    return (
      <ProtectedScreenFallback
        loadingMessage="Загрузка…"
        telegramMessage="Здоровье доступно в Telegram Mini App."
      />
    );
  }

  const profile = initData
    ? getCached<NutritionProfileData>(cacheKey.nutritionProfile())
    : null;
  const selected = initData
    ? getCached<{ menu: MenuVariant | null }>(cacheKey.selectedMenu(mode))
    : null;
  const pantry = initData
    ? getCached<PantryList>(cacheKey.pantry(mode))
    : null;

  const advice = pickMainAdvice({
    profile,
    menu: selected?.menu ?? null,
    pantry,
    pantryActiveCount: pantry?.active_count ?? 0,
  });

  return (
    <SectionHub
      title="Здоровье"
      subtitle="Спокойный помощник по питанию"
      lead={
        <div className="pa-card p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
            Здоровье сегодня
          </p>
          <p className="mt-1.5 text-base font-bold text-graphite-900">
            {advice.title}
          </p>
          <p className="mt-1 text-sm text-graphite-500">{advice.body}</p>
        </div>
      }
    >
      <HubTile
        href="/health/today"
        icon="📊"
        title="Сегодня"
        hint="КБЖУ, вода и совет дня"
        tone="primary"
      />
      <HubTile
        href={withReturnTo("/profile/nutrition", HEALTH_RETURN)}
        icon="🎯"
        title="Цели"
        hint="Цель питания и ограничения"
      />
      <HubTile
        href={withReturnTo("/progress", HEALTH_RETURN)}
        icon="📈"
        title="Прогресс"
        hint="Вес, тренировки, динамика"
      />
      <HubTile
        href="/health/chat"
        icon="✨"
        title="AI-рекомендации"
        hint="Спросить ПланАм о питании"
      />
    </SectionHub>
  );
}
