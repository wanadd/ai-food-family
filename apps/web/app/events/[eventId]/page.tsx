import { EventDetailV2 } from "@/components/planam-v2/events/EventDetailV2";

export default function EventDetailPage({ params }: { params: { eventId: string } }) {
  return <EventDetailV2 eventId={params.eventId} />;
}
