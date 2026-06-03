import { Card2026 } from "@/components/planam-2026/ui/Card2026";

export type RoutePlaceholder2026Props = {
  title: string;
  description: string;
  sprintNote?: string;
};

export function RoutePlaceholder2026({
  title,
  description,
  sprintNote,
}: RoutePlaceholder2026Props) {
  return (
    <div className="mx-auto max-w-lg px-4 py-6">
      <Card2026>
        <p className="pa26-section-title">{title}</p>
        <p className="pa26-body mt-2 text-pa-muted">{description}</p>
        {sprintNote ? (
          <p className="pa26-micro mt-4 text-warm">{sprintNote}</p>
        ) : null}
      </Card2026>
    </div>
  );
}
