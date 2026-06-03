import { InsightCard2026 } from "@/components/planam-2026/cards/InsightCard2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";

type AIInsight2026Props = {
  text: string | null;
  loading?: boolean;
  healthRelated?: boolean;
};

export function AIInsight2026({
  text,
  loading = false,
  healthRelated = false,
}: AIInsight2026Props) {
  if (loading) {
    return (
      <section className="px-4 pt-4" aria-busy="true">
        <Skeleton2026 variant="rect" className="h-20 w-full" />
      </section>
    );
  }

  if (!text) {
    return null;
  }

  return (
    <section className="px-4 pt-4" aria-label="Совет ПланАм">
      <InsightCard2026
        emoji="💡"
        disclaimer={
          healthRelated
            ? "Рекомендация, не медицинское назначение"
            : undefined
        }
      >
        <span className="line-clamp-2">{text}</span>
      </InsightCard2026>
    </section>
  );
}
