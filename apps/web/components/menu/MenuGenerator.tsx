"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { ReplaceDishModal } from "@/components/menu/ReplaceDishModal";
import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchSelectedMenu,
  generateMenus,
  replaceDish,
  selectMenu,
} from "@/lib/menu/api";
import { VARIANT_LABELS } from "@/lib/menu/labels";
import type { MenuVariant, MenuVariantType } from "@/lib/menu/types";

function SelectedMenuSkeleton() {
  return (
    <section
      className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5"
      aria-busy="true"
      aria-label="Проверяем выбранное меню"
    >
      <p className="text-center text-sm font-medium text-stone-600">
        Проверяем выбранное меню…
      </p>
      <div className="mt-4 space-y-3">
        <div className="h-24 rounded-xl bg-stone-100" />
        <div className="h-4 w-3/4 rounded bg-stone-100" />
        <div className="h-4 w-1/2 rounded bg-stone-100" />
      </div>
    </section>
  );
}

export function MenuGenerator() {
  const { initData, isTelegram } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const [menus, setMenus] = useState<MenuVariant[]>([]);
  const [activeVariant, setActiveVariant] = useState<MenuVariantType>("quick");
  const [contextLabel, setContextLabel] = useState("");
  const [membersCount, setMembersCount] = useState(0);
  const [generatedWithAi, setGeneratedWithAi] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<MenuVariantType | null>(
    null,
  );
  const [loadingSelectedMenu, setLoadingSelectedMenu] = useState(true);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<MenuVariant | null>(null);

  const isCheckingSelectedMenu = loadingSelectedMenu || modeLoading;

  const applySelectedMenu = useCallback((menu: MenuVariant) => {
    setSelectedVariant(menu.variant);
    setActiveVariant(menu.variant);
    setMenus([menu]);
  }, []);

  const loadSelectedMenu = useCallback(
    async (telegramInitData: string, appMode: typeof mode) => {
      setLoadingSelectedMenu(true);
      setError(null);
      try {
        const selected = await fetchSelectedMenu(telegramInitData, appMode);
        if (selected?.menu) {
          applySelectedMenu(selected.menu);
        } else {
          setSelectedVariant(null);
          setMenus([]);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Не удалось загрузить сохранённое меню",
        );
        setSelectedVariant(null);
        setMenus([]);
      } finally {
        setLoadingSelectedMenu(false);
      }
    },
    [applySelectedMenu],
  );

  useEffect(() => {
    if (modeLoading) {
      setLoadingSelectedMenu(true);
      return;
    }

    if (!initData) {
      if (!isTelegram) {
        setLoadingSelectedMenu(false);
        setMenus([]);
        setSelectedVariant(null);
      } else {
        setLoadingSelectedMenu(true);
      }
      return;
    }

    void loadSelectedMenu(initData, mode);
  }, [initData, mode, modeLoading, isTelegram, loadSelectedMenu]);

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
      const saved = await selectMenu(initData, mode, menu);
      applySelectedMenu(saved.menu);
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
      if (selectedVariant === updated.variant) {
        applySelectedMenu(updated);
      }
      setReplaceTarget(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось заменить блюдо",
      );
    } finally {
      setLoading(false);
    }
  }

  const activeMenu =
    menus.find((menu) => menu.variant === activeVariant) ?? menus[0];
  const hasMultipleVariants = menus.length > 1;
  const hasSavedMenu = menus.length > 0 && !generating;

  if (!initData && !isTelegram && !isCheckingSelectedMenu) {
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
    <div className="min-h-screen bg-white">
      <header className="border-b border-stone-100 bg-white px-5 py-6">
        <h1 className="text-2xl font-bold text-stone-900">Меню</h1>
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

        {isCheckingSelectedMenu ? <SelectedMenuSkeleton /> : null}

        {!isCheckingSelectedMenu && hasSavedMenu ? (
          <>
            {selectedVariant && !hasMultipleVariants ? (
              <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                Сохранённое меню — останется после перезагрузки приложения.
              </p>
            ) : null}

            {hasMultipleVariants ? (
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
                      const hasVariant = menus.some(
                        (menu) => menu.variant === variant,
                      );
                      if (!hasVariant) {
                        return null;
                      }
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
              </>
            ) : null}

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
        ) : null}

        {!isCheckingSelectedMenu ? (
          <section className="rounded-2xl border border-stone-200 bg-white p-5">
            <p className="text-sm text-stone-600">
              Учитываются ваш onboarding, остатки, цели, диеты, аллергии, бюджет и
              время готовки. В семейном режиме — данные всех участников.
            </p>
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating || !initData}
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3.5 text-sm font-semibold text-white shadow-md transition hover:opacity-95 disabled:opacity-50"
            >
              {generating ? "Генерация меню…" : "Сгенерировать меню на день"}
            </button>
            {!hasSavedMenu ? (
              <p className="mt-3 text-center text-xs text-stone-400">
                Выберите вариант и нажмите «Выбрать меню», чтобы сохранить его и
                собрать список покупок
              </p>
            ) : null}
          </section>
        ) : null}
      </main>

      <BottomBackButton className="pb-4 pt-2" />

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
