import { ResultsView } from "@/components/results-view";

export default async function ResultsPage({
  params,
}: {
  params: Promise<{ id: string; analysisId: string }>;
}) {
  const { id, analysisId } = await params;
  return <ResultsView id={id} analysisId={analysisId} />;
}
