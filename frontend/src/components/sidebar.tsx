"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useProcesses } from "@/lib/api/queries";
import { steps, version } from "@/lib/format";

import { BrandIcon } from "./brand-icon";
import { buttonClass } from "./button";

// The sidebar of the vanilla client (ADR 0014): brand, new process, and every process one
// click away, the current one marked. On narrow screens it folds above the page.
export function Sidebar() {
  const processes = useProcesses();
  const pathname = usePathname();

  return (
    <aside className="flex flex-col gap-3 border-b border-line bg-sidebar p-4 md:sticky md:top-0 md:h-screen md:gap-5 md:border-r md:border-b-0 md:px-[18px] md:pt-7 md:pb-5">
      <Link href="/" className="flex items-center gap-2.5 text-ink no-underline hover:no-underline">
        <BrandIcon className="size-9 shrink-0" />
        <span className="leading-tight">
          <span className="block text-lg font-semibold tracking-tight">Process Discovery</span>
          <span className="mt-1 block text-[9px] tracking-[2px] text-muted uppercase">
            Automation planner
          </span>
        </span>
      </Link>
      <Link href="/processes/new" className={`${buttonClass("primary")} w-full`}>
        + New process
      </Link>
      <nav
        aria-labelledby="nav-title"
        className="min-h-0 flex-1 border-t border-line pt-3 md:overflow-y-auto"
      >
        <h2
          id="nav-title"
          className="mx-2.5 mb-2 hidden text-[10px] font-semibold tracking-[2px] text-muted uppercase md:block"
        >
          Processes
        </h2>
        {processes.data?.length === 0 && (
          <p className="mx-2.5 text-sm text-muted">No processes yet.</p>
        )}
        <ul className="flex gap-1.5 overflow-x-auto md:block md:space-y-0.5">
          {processes.data?.map((process) => {
            const href = `/processes/${process.id}`;
            const current = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={process.id} className="flex-none md:flex-auto">
                <Link
                  href={href}
                  aria-current={current ? "page" : undefined}
                  className="block max-w-56 rounded-control px-2.5 py-2 text-sm text-ink-soft no-underline hover:bg-surface-raised hover:no-underline aria-[current=page]:bg-accent-soft aria-[current=page]:text-accent md:max-w-none"
                >
                  <span className="block truncate">{process.name}</span>
                  <span className="block text-[11px] text-muted">
                    {steps(process.step_count)} · {version(process.version)}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <p className="hidden border-t border-line pt-4 text-[11px] text-muted md:block">
        Deterministic first. The LLM interprets; it never produces a number.
      </p>
    </aside>
  );
}
