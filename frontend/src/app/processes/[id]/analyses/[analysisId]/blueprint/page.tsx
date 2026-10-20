import { BlueprintView } from "@/components/blueprint-view";

export default async function BlueprintPage({
  params,
}: {
  params: Promise<{ id: string; analysisId: string }>;
}) {
  const { id, analysisId } = await params;
  return <BlueprintView id={id} analysisId={analysisId} />;
}
