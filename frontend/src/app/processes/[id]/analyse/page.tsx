import { AnalyseView } from "@/components/analyse-view";

export default async function AnalysePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AnalyseView id={id} />;
}
