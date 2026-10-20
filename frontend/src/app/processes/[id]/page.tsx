import { StepsView } from "@/components/steps-view";

export default async function StepsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <StepsView id={id} />;
}
