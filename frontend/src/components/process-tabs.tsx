"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAnalyses } from "@/lib/api/queries";

// The sections of a process, as the tabs of web/process-views.js. Results and Blueprint
// open the analysis on screen, else the latest one; with no analysis yet they stay
// disabled and say why.

type Tab = { key: string; title: string; href: string | null };

const ANALYSIS = /\/analyses\/([^/]+)(\/blueprint)?$/;
export const NO_ANALYSIS = "Run an analysis first";

function active(pathname: string, base: string): string {
  const match = pathname.match(ANALYSIS);
  if (match) return match[2] ? "blueprint" : "results";
  if (pathname === `${base}/analyse`) return "analyse";
  if (pathname === `${base}/history`) return "history";
  return "steps";
}

export function ProcessTabs({ processId }: { processId: string }) {
  const pathname = usePathname();
  const analyses = useAnalyses(processId);
  const base = `/processes/${processId}`;
  const analysisId = pathname.match(ANALYSIS)?.[1] ?? analyses.data?.[0]?.id;
  const analysis = analysisId ? `${base}/analyses/${analysisId}` : null;
  const current = active(pathname, base);

  const tabs: Tab[] = [
    { key: "steps", title: "Steps", href: base },
    { key: "analyse", title: "Analyse", href: `${base}/analyse` },
    { key: "results", title: "Results", href: analysis },
    { key: "blueprint", title: "Blueprint", href: analysis && `${analysis}/blueprint` },
    { key: "history", title: "History", href: `${base}/history` },
  ];

  const look =
    "block border-b-2 border-transparent px-4 py-2.5 text-sm font-semibold whitespace-nowrap text-muted no-underline";
  return (
    <nav aria-label="Process sections" className="mb-7 border-b border-line">
      <ul className="flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <li key={tab.key}>
            {tab.href ? (
              <Link
                href={tab.href}
                aria-current={tab.key === current ? "page" : undefined}
                className={`${look} hover:text-ink hover:no-underline aria-[current=page]:border-accent aria-[current=page]:text-accent`}
              >
                {tab.title}
              </Link>
            ) : (
              <>
                <span
                  role="link"
                  aria-disabled="true"
                  aria-describedby={`${tab.key}-tab-why`}
                  title={NO_ANALYSIS}
                  className={`${look} cursor-not-allowed opacity-45`}
                >
                  {tab.title}
                </span>
                <span id={`${tab.key}-tab-why`} className="sr-only">
                  {NO_ANALYSIS}
                </span>
              </>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
