"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { ReplaceDishModal } from "@/components/menu/ReplaceDishModal";
import {
  fetchSelectedMenu,
  generateMenus,
  replaceDish,
  selectMenu,
} from "@/lib/menu/api";
import { VARIANT_LABELS } from "@/lib/menu/labels";
import type { MenuVariant, MenuVariantType } from "@/lib/menu/types";
import { getTelegramInitData } from "@/lib/telegram-webapp";

export function MenuGenerator() {
  const { mode } = useAppMode();
  const [initData, setInitData] = useState("");
  const [menus, setMenus] = useState<MenuVariant[]>([]);
  const [activeVariant, setActiveVariant] = useState<MenuVariantType>("quick");
  const [contextLabel, setContextLabel] = useState("");
  const [membersCount, setMembersCount] = useState(0);
  const [generatedWithAi, setGeneratedWithAi] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<MenuVariantType | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<MenuVariant | null>(null);

  const loadSelected = useCallback(
    async (telegramInitData: string, appMode: typeof mode) => {
      const selected = await fetchSelectedMenu(telegramInitData, appMode);
      setSelectedVariant(selected?.variant ?? null);
    },
    [],
  );

  useEffect(() => {
    const data = getTelegramInitData();
    setInitData(data);
    setMenus([]);
    if (data) {
      loadSelected(data, mode);
    }
  }, [loadSelected, mode]);

  async function handleGenerate() {
    if (!initData) {
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const result = await generateMenus(initData, mode);
      setMenus(result.menus);
      setContextLabel(result.context_label);
      setMembersCount(result.members_count);
      setGeneratedWithAi(result.generated_with_ai);
      setActiveVariant("quick");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось сгенерировать меню",
      );
    } finally {
      setGenerating(false);
    }
  }

  async function handleSelect(menu: MenuVariant) {
    if (!initData) {
      return;
    }
    setSelecting(true);
    setError(null);
    try {
      await selectMenu(initData, mode, menu);
      setSelectedVariant(menu.variant);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось сохранить выбор",
      );
    } finally {
      setSelecting(false);
    }
  }

  async function handleReplace(mealIndex: number) {
    if (!initData || !replaceTarget) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const updated = await replaceDish(
        initData,
        mode,
        replaceTarget,
        mealIndex,
      );
      setMenus((prev) =>
        prev.map((item) =>
          item.variant === updated.variant ? updated : item,
        ),
      );
      setReplaceTarget(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось заменить блюдо",
      );
    } finally {
      setLoading(false);
    }
  }

  const activeMenu = menus.find((menu) => menu.variant === activeVariant);

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Генерация меню доступна в Telegram Mini App после авторизации.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <header className="border-b border-stone-200/80 bg-white/80 px-5 py-6 backdrop-blur">
        <Link href="/" className="text-xs font-semibold text-emerald-700">
          ← Назад
        </Link>
        <h1 className="mt-3 text-2xl font-bold text-stone-900">AI Меню</h1>
        <p className="mt-1 text-sm text-stone-500">
          Три варианта на день с учётом вашего профиля и ограничений
        </p>
        <div className="mt-3 flex gap-4 text-xs font-semibold">
          <Link href="/pantry" className="text-teal-700">
            Остатки →
          </Link>
          <Link href="/shopping" className="text-amber-800">
            Список покупок →
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-6 px-5 py-8">
        <ModeBanner />
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <section className="rounded-2xl border border-stone-200 bg-white p-5">
          <p className="text-sm text-stone-600">
            Учитываются ваш onboarding, остатки, цели, диеты, аллергии, бюджет и
            время готовки. В семейном режиме — данные всех участников.
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="mt-4 w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3.5 text-sm font-semibold text-white shadow-md transition hover:opacity-95 disabled:opacity-50"
          >
            {generating ? "Генерация меню…" : "Сгенерировать меню на день"}
          </button>
        </section>

        {menus.length > 0 ? (
          <>
            <div className="flex items-center justify-between text-sm">
              <p className="text-stone-600">
                {contextLabel}
                {membersCount > 1 ? ` · ${membersCount} чел.` : ""}
              </p>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  generatedWithAi
                    ? "bg-violet-100 text-violet-800"
                    : "bg-stone-100 text-stone-600"
                }`}
              >
                {generatedWithAi ? "OpenAI" : "Демо-режим"}
              </span>
            </div>

            <div
              className="flex gap-2 rounded-2xl bg-stone-100 p-1"
              role="tablist"
              aria-label="Варианты меню"
            >
              {(Object.keys(VARIANT_LABELS) as MenuVariantType[]).map(
                (variant) => {
                  const meta = VARIANT_LABELS[variant];
                  const isActive = activeVariant === variant;
                  return (
                    <button
                      key={variant}
                      type="button"
                      role="tab"
                      aria-selected={isActive}
                      onClick={() => setActiveVariant(variant)}
                      className={`flex-1 rounded-xl py-2.5 text-center text-xs font-semibold transition ${
                        isActive
                          ? "bg-white text-stone-900 shadow-sm"
                          : "text-stone-500"
                      }`}
                    >
                      <span className="mr-1" aria-hidden>
                        {meta.emoji}
                      </span>
                      {meta.label}
                    </button>
                  );
                },
              )}
            </div>

            {activeMenu ? (
              <MenuVariantCard
                menu={activeMenu}
                selected={selectedVariant === activeMenu.variant}
                onSelect={() => handleSelect(activeMenu)}
                onReplace={() => setReplaceTarget(activeMenu)}
                selecting={selecting}
              />
            ) : null}
          </>
        ) : (
          <p className="text-center text-sm text-stone-400">
            Нажмите кнопку выше, чтобы получить три варианта меню
          </p>
        )}
      </main>

      {replaceTarget ? (
        <ReplaceDishModal
          menu={replaceTarget}
          onClose={() => !loading && setReplaceTarget(null)}
          onReplace={handleReplace}
          loading={loading}
        />
      ) : null}
    </div>
  );
}
