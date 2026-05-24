import { AdminUserDetailPage } from "@/components/admin/AdminUserDetailPage";

export default function AdminUserDetailRoute({
  params,
}: {
  params: { id: string };
}) {
  const userId = Number(params.id);
  if (!Number.isFinite(userId)) {
    return <p className="p-4 text-sm text-stone-600">Некорректный id</p>;
  }
  return <AdminUserDetailPage userId={userId} />;
}
