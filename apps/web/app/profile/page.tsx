import Link from "next/link";

import { ModeSwitcher } from "@/components/app-mode/ModeSwitcher";

const MORE_LINKS = [
  { href: "/onboarding", label: "Настройки питания", desc: "Цели, диеты, ограничения" },
  { href: "/family", label: "Семья", desc: "Семейный режим и участники" },
  { href: "/pantry", label: "Остатки", desc: "Продукты дома для AI меню" },
  { href: "/recipes", label: "Рецепты", desc: "Каталог и избранное" },
  { href: "/notifications", label: "Уведомления", desc: "Напоминания о покупках и готовке" },
] as const;

export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <header className="px-5 pb-2 pt-8">
        <h1 className="text-2xl font-bold text-stone-900">Профиль</h1>
        <p className="mt-1 text-sm text-stone-500">ПланАм — настройки и разделы</p>
      </header>

      <main className="mx-auto max-w-lg space-y-5 px-5 pb-8">
        <section className="rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
            Режим
          </p>
          <div className="mt-3">
            <ModeSwitcher />
          </div>
        </section>

        <section className="space-y-3">
          <p className="px-1 text-xs font-bold uppercase tracking-wide text-stone-500">
            Ещё
          </p>
          {MORE_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm transition hover:border-emerald-200"
            >
              <p className="font-semibold text-stone-900">{item.label}</p>
              <p className="mt-1 text-sm text-stone-500">{item.desc}</p>
            </Link>
          ))}
        </section>
      </main>
    </div>
  );
}
