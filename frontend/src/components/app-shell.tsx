import type { ReactNode } from "react";

import { DemoBanner } from "./demo-banner";
import { Sidebar } from "./sidebar";

// Every page: skip link, the sidebar, the public demo banner and one main region, laid out
// as in the vanilla client (ADR 0014).
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <a
        href="#main"
        className="fixed -top-16 left-2 z-50 rounded-control bg-surface p-3 focus:top-2"
      >
        Skip to content
      </a>
      <div className="min-h-screen md:grid md:grid-cols-[268px_minmax(0,1fr)]">
        <Sidebar />
        <div className="min-w-0">
          <DemoBanner />
          <main
            id="main"
            tabIndex={-1}
            className="mx-auto max-w-[1320px] px-4 pt-6 pb-12 outline-none md:px-11 md:pt-10 md:pb-16"
          >
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
