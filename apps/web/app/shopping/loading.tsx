import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function ShoppingLoading() {
  return (
    <ScreenLayout title="Покупки" contentClassName="space-y-3 pb-24">
      <SkeletonList count={3} />
    </ScreenLayout>
  );
}
