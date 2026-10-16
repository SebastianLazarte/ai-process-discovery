import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { ProcessForm } from "@/components/process-form";

export const metadata: Metadata = { title: "New process · AI Process Discovery" };

export default function NewProcessPage() {
  return (
    <>
      <Breadcrumbs items={[{ label: "Processes", href: "/" }, { label: "New process" }]} />
      <h1 className="mt-4 text-2xl font-semibold">New process</h1>
      <p className="mt-2 mb-6 text-gray-700">
        Describe the process; you add its steps on the next page.
      </p>
      <ProcessForm />
    </>
  );
}
