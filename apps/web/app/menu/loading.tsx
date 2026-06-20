import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function MenuLoading() {
  return (
    <ScreenLayout title="Меню" contentClassName="space-y-3 pb-24">
      <SkeletonList count={3} />
    </ScreenLayout>
  );
}
