"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { ReplaceDishModal } from "@/components/menu/ReplaceDishModal";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchSelectedMenu,
  replaceDish,
  selectMenu,
} from "@/lib/menu/api";
import type { MenuVariant } from "@/lib/menu/types";

export function MenuCurrentView() {
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [selectedAt, setSelectedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [replacing, setReplacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<MenuVariant | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const selected = await fetchSelectedMenu(initData, mode);
      setMenu(selected?.menu ?? null);
      setSelectedAt(selected?.selected_at ?? null);
    } catch {
      setError("Не удалось загрузить план");
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) return;
    void load();
  }, [load, modeLoading]);

  async function handleReplace(mealIndex: number) {
    if (!initData || !replaceTarget || !menu) return;
    setReplacing(true);
    setError(null);
    try {
      const updated = await replaceDish(
        initData,
        mode,
        replaceTarget,
        mealIndex,
      );
      await selectMenu(initData, mode, updated);
      setMenu(updated);
      setReplaceTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось заменить блюдо");
    } finally {
      setReplacing(false);
    }
  }

  if (loading || modeLoading) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка плана…" />
      </div>
    );
  }

  if (!menu) {
    return (
      <div className="min-h-screen bg-stone-50 px-4 py-16 text-center">
        <p className="text-stone-600">Активного плана пока нет</p>
        <Link
          href="/menu"
          className="mt-4 inline-block text-sm font-semibold text-emerald-700"
        >
          Настроить план
        </Link>
        <BottomBackButton className="mt-6" />
      </div>
    );
  }

  const dateLabel = selectedAt
    ? new Date(selectedAt).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "long",
      })
    : "Сегодня";

  return (
    <div className="min-h-screen bg-stone-50 pb-24">
      <header className="border-b border-stone-100 bg-white px-4 py-4">
        <div className="mx-auto max-w-lg">
          <Link
            href="/menu"
            className="text-sm font-semibold text-emerald-700"
          >
            ← Настройки плана
          </Link>
          <h1 className="mt-2 text-xl font-bold text-stone-900">
            {menu.title}
          </h1>
          <p className="mt-1 text-sm text-stone-500">
            {dateLabel} · активен
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-4 py-4">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}

        <MenuVariantCard
          menu={menu}
          selected
          onSelect={() => {}}
          onReplace={() => setReplaceTarget(menu)}
          selecting={false}
        />
      </main>

      <BottomBackButton className="pb-2 pt-2" />

      {replaceTarget ? (
        <ReplaceDishModal
          menu={replaceTarget}
          onClose={() => !replacing && setReplaceTarget(null)}
          onReplace={handleReplace}
          loading={replacing}
        />
      ) : null}
    </div>
  );
}
