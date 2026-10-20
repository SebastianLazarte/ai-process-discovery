import type { ReactNode } from "react";

import { ProcessView } from "@/components/process-view";

// Every section of a process shares its title and tabs; each page renders one section.
export default async function ProcessLayout({
  params,
  children,
}: {
  params: Promise<{ id: string }>;
  children: ReactNode;
}) {
  const { id } = await params;
  return <ProcessView id={id}>{children}</ProcessView>;
}
