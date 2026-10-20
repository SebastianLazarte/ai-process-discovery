import { version } from "@/lib/format";

import { Eyebrow } from "./panel";

// The title of every process page, as processHeader in web/process-views.js.
export function ProcessHeader({
  process,
}: {
  process: { name: string; description?: string; version: number };
}) {
  return (
    <header className="mb-6">
      <Eyebrow>Process · {version(process.version)}</Eyebrow>
      <h1 className="mb-3 text-[27px] leading-[1.15] font-semibold tracking-[-1.1px] md:text-[34px]">
        {process.name}
      </h1>
      {process.description && (
        <p className="max-w-[760px] text-[15px] text-muted">{process.description}</p>
      )}
    </header>
  );
}
