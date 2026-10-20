import { HistoryView } from "@/components/history-view";

export default async function HistoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <HistoryView id={id} />;
}
