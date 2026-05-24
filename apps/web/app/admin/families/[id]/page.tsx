import { AdminFamilyDetailPage } from "@/components/admin/AdminFamilyDetailPage";

export default function AdminFamilyDetailRoute({
  params,
}: {
  params: { id: string };
}) {
  const familyId = Number(params.id);
  if (!Number.isFinite(familyId)) {
    return <p className="p-4 text-sm text-stone-600">Некорректный id</p>;
  }
  return <AdminFamilyDetailPage familyId={familyId} />;
}
