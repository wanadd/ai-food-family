import Link from "next/link";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";

type SettingsPlaceholderProps = {
  title: string;
  description: string;
};

export function SettingsPlaceholder({
  title,
  description,
}: SettingsPlaceholderProps) {
  return (
    <SettingsScaffold title={title}>
      <section className="rounded-2xl border border-stone-100 bg-white p-5 shadow-sm">
        <p className="text-sm leading-relaxed text-stone-600">{description}</p>
        <p className="mt-4 text-sm font-semibold text-emerald-700">
          Раздел появится в одном из следующих обновлений.
        </p>
      </section>
      <p className="text-center text-sm text-stone-500">
        <Link href="/settings" className="font-semibold text-emerald-700">
          ← К настройкам
        </Link>
      </p>
    </SettingsScaffold>
  );
}
