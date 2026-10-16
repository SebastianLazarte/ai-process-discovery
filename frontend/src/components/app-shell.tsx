import Link from "next/link";
import type { ReactNode } from "react";

import { buttonClass } from "./button";
import { DemoBanner } from "./demo-banner";

// Every page: skip link, the public demo banner, the top bar and one main region.
// Navigation is a top bar with breadcrumbs, no sidebar (docs/design/00-brief.md).
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:bg-white focus:p-2"
      >
        Skip to content
      </a>
      <DemoBanner />
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <Link href="/" className="font-semibold no-underline">
            Process Discovery
          </Link>
          <nav aria-label="Main" className="flex items-center gap-2">
            <Link href="/" className="hidden px-2 sm:inline">
              Processes
            </Link>
            <Link href="/processes/new" className={buttonClass("primary")}>
              New process
            </Link>
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="mx-auto max-w-5xl px-4 py-8">
        {children}
      </main>
    </>
  );
}
