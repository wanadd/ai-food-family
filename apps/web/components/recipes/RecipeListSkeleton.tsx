/**
 * Скелетон списка рецептов в форме карточки (BALANCED ONE SCREEN UX):
 * заполняет высоту во время загрузки, повторяя структуру RecipeCard —
 * заголовок, две строки описания и ряд «таблеток».
 */
export function RecipeListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3" aria-label="Загрузка рецептов" aria-busy>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="pa-card animate-pulse p-4">
          <div className="h-4 w-2/3 rounded bg-cream-border" />
          <div className="mt-2.5 h-3 w-full rounded bg-cream-border" />
          <div className="mt-1.5 h-3 w-4/5 rounded bg-cream-border" />
          <div className="mt-3 flex gap-2">
            <div className="h-6 w-16 rounded-pill bg-cream-border" />
            <div className="h-6 w-14 rounded-pill bg-cream-border" />
            <div className="h-6 w-12 rounded-pill bg-cream-border" />
          </div>
        </div>
      ))}
    </div>
  );
}
