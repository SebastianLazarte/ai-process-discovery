import type { Metadata } from "next";

import { Eyebrow, Panel } from "@/components/panel";
import { ProcessForm } from "@/components/process-form";

export const metadata: Metadata = { title: "New process · AI Process Discovery" };

export default function NewProcessPage() {
  return (
    <>
      <header className="mb-6">
        <Eyebrow>New process</Eyebrow>
        <h1 className="mb-3 text-[27px] leading-[1.15] font-semibold tracking-[-1.1px] md:text-[34px]">
          Describe the process
        </h1>
        <p className="max-w-[760px] text-[15px] text-muted">
          You add its steps on the next page. Leave a figure empty when you do not know it.
        </p>
      </header>
      <Panel id="new-process-title" title="Process" className="max-w-3xl">
        <ProcessForm />
      </Panel>
    </>
  );
}
