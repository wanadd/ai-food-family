import type { ReactNode } from "react";

type MenuPlannerSectionProps = {
  title: string;
  action?: ReactNode;
  children: ReactNode;
};

export function MenuPlannerSection({
  title,
  action,
  children,
}: MenuPlannerSectionProps) {
  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-bold text-stone-900">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
