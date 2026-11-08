"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useProcesses } from "@/lib/api/queries";
import { steps, version } from "@/lib/format";

import { BrandIcon } from "./brand-icon";
import { buttonClass } from "./button";
import { PlusIcon, ProcessesIcon } from "./icons";
import { EmptyState, ProcessListSkeleton } from "./states";

// The navigation in two forms (ADR 0018). Home and New process keep the full sidebar of
// ADR 0014: brand, New process, and every process one click away, the current one marked.
// Inside a process it steps aside to a rail of icons, so the results get the width, and
// the process list opens from the rail. On a narrow screen both fold above the page.

const PROCESS_PAGE = /^\/processes\/(?!new(?:\/|$))[^/]+/;

/** True on any page of one process, where the rail replaces the sidebar. */
export function isProcessPage(pathname: string): boolean {
  return PROCESS_PAGE.test(pathname);
}

export function Sidebar() {
  const pathname = usePathname();
  return isProcessPage(pathname) ? <Rail pathname={pathname} /> : <FullSidebar />;
}

function FullSidebar() {
  return (
    <aside className="flex flex-col gap-4 bg-sidebar p-4 md:sticky md:top-0 md:h-screen md:w-[268px] md:gap-6 md:px-[18px] md:pt-7 md:pb-5">
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
        <PlusIcon />
        New process
      </Link>
      <nav aria-labelledby="nav-title" className="min-h-0 flex-1 md:overflow-y-auto">
        <h2
          id="nav-title"
          className="mx-2.5 mb-2 hidden text-[10px] font-semibold tracking-[2px] text-muted uppercase md:block"
        >
          Processes
        </h2>
        <ProcessList layout="fold" />
      </nav>
      <p className="hidden text-[11px] text-muted md:block">
        Deterministic first. The LLM interprets; it never produces a number.
      </p>
    </aside>
  );
}

// The rail. Each control is an icon with its accessible name, shown again as a tooltip.
const railItem =
  "inline-flex size-11 items-center justify-center rounded-control text-ink-soft no-underline transition-colors duration-150 hover:bg-surface-raised hover:text-ink hover:no-underline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-accent aria-expanded:bg-surface-raised aria-expanded:text-ink";
const brandItem =
  "inline-flex size-11 items-center justify-center rounded-control no-underline hover:no-underline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-accent";

function Rail({ pathname }: { pathname: string }) {
  // The list is open for the page it was opened on: moving to another page closes it.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const open = openOn === pathname;
  const rail = useRef<HTMLElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (focusToggle: boolean) => {
      setOpenOn(null);
      if (focusToggle) toggle.current?.focus();
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close(true);
    };
    const onPointer = (event: PointerEvent) => {
      if (!rail.current?.contains(event.target as Node)) close(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open]);

  return (
    <aside
      ref={rail}
      className="relative z-30 bg-sidebar p-2 md:sticky md:top-0 md:h-screen md:w-[72px] md:px-3.5 md:pt-6"
    >
      <ul aria-label="Navigation" className="flex items-center gap-1 md:flex-col md:gap-2">
        <li className="md:mb-3">
          <Link href="/" aria-label="Home" title="Home" className={brandItem}>
            <BrandIcon className="size-9" />
          </Link>
        </li>
        <li>
          <Link
            href="/processes/new"
            aria-label="New process"
            title="New process"
            className={railItem}
          >
            <PlusIcon />
          </Link>
        </li>
        <li>
          <button
            ref={toggle}
            type="button"
            aria-label="Processes"
            title="Processes"
            aria-expanded={open}
            aria-controls="rail-processes"
            onClick={() => setOpenOn(open ? null : pathname)}
            className={railItem}
          >
            <ProcessesIcon />
          </button>
        </li>
      </ul>
      <nav
        id="rail-processes"
        aria-label="Processes"
        hidden={!open}
        className="mt-2 max-h-[70vh] overflow-y-auto rounded-panel bg-surface-raised p-2 md:absolute md:top-4 md:left-full md:mt-0 md:ml-2 md:max-h-[calc(100vh-2rem)] md:w-[268px]"
      >
        <h2 className="mx-2.5 mt-1 mb-2 text-[10px] font-semibold tracking-[2px] text-muted uppercase">
          Processes
        </h2>
        <ProcessList layout="stack" />
      </nav>
    </aside>
  );
}

/**
 * Every process, the one on screen marked. In the full sidebar the list scrolls sideways
 * inside itself on a narrow screen ("fold"); in the panel of the rail it always stacks.
 */
function ProcessList({ layout }: { layout: "fold" | "stack" }) {
  const processes = useProcesses();
  const pathname = usePathname();
  const fold = layout === "fold";

  if (processes.isPending) return <ProcessListSkeleton fold={fold} />;
  if (processes.data?.length === 0) {
    return (
      <EmptyState
        compact
        title="No processes yet"
        action={
          <>
            <Link href="/processes/new">Start from your sector</Link>
            <Link href="/#demos-title">Open a demo</Link>
          </>
        }
      >
        Start one, or open a finished demo.
      </EmptyState>
    );
  }
  return (
    <ul className={fold ? "flex gap-1.5 overflow-x-auto md:block md:space-y-0.5" : "space-y-0.5"}>
      {processes.data?.map((process) => {
        const href = `/processes/${process.id}`;
        const current = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <li key={process.id} className={fold ? "flex-none md:flex-auto" : undefined}>
            <Link
              href={href}
              aria-current={current ? "page" : undefined}
              className={`block rounded-control px-2.5 py-2 text-sm text-ink-soft no-underline hover:bg-surface-hover hover:no-underline aria-[current=page]:bg-accent-soft aria-[current=page]:text-accent ${fold ? "max-w-56 md:max-w-none" : ""}`}
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
  );
}
