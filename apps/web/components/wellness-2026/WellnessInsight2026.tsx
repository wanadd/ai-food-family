import { InsightCard2026 } from "@/components/planam-2026/cards/InsightCard2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";

type WellnessInsight2026Props = {
  text: string | null;
  loading?: boolean;
};

export function WellnessInsight2026({
  text,
  loading = false,
}: WellnessInsight2026Props) {
  if (loading) {
    return <Skeleton2026 variant="rect" className="h-20 w-full" />;
  }

  if (!text) {
    return null;
  }

  return (
    <section aria-label="Рекомендация">
      <p className="pa26-micro mb-2 font-semibold uppercase tracking-wide text-pa-muted">
        Совет дня
      </p>
      <InsightCard2026
        emoji="✨"
        disclaimer="Рекомендация, не медицинское назначение"
      >
        <span className="line-clamp-2">{text}</span>
      </InsightCard2026>
    </section>
  );
}
