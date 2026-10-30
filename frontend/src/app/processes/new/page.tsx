import type { Metadata } from "next";

import { Eyebrow } from "@/components/panel";
import { TemplateStart } from "@/components/template-start";

export const metadata: Metadata = { title: "New process · AI Process Discovery" };

export default function NewProcessPage() {
  return (
    <>
      <header className="mb-6">
        <Eyebrow>New process</Eyebrow>
        <h1 className="mb-3 text-[27px] leading-[1.15] font-semibold tracking-[-1.1px] md:text-[34px]">
          Start from your sector
        </h1>
        <p className="max-w-[760px] text-[15px] text-muted">
          Pick a common process of your sector and review its steps: you only type the numbers of
          your company. Choose Other to describe a process yourself. Leave a figure empty when you
          do not know it.
        </p>
      </header>
      <TemplateStart />
    </>
  );
}
