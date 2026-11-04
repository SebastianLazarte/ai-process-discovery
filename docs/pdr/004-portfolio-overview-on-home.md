# PDR 004: Portfolio overview on Home

**Status:** accepted · 2026-11-03

## Problem

Home lists processes by name, owner, runs per month, steps, version and date. Nothing on it says how much time or money those processes consume, so an operations lead who comes back with several processes cannot tell how much is at stake, or which process weighs most, without opening each analysis in turn. On the public demo the list also holds the processes of every other visitor, so even a total would mix strangers' data with the visitor's own.

## Decision

Block B18, "Portfolio overview", after B17 (Graphite) and before B15 (the analysis dashboard of PDR 003). It serves the operations lead (PDR 002) and the current cost baseline of epic RU-02.

- **One question: how much is at stake.** A band at the top of Home shows the monthly hours and the monthly cost that this browser's processes consume today, and one horizontal bar per process with its monthly cost, ordered by the API from the largest.
- **The figures come from the latest analysis** of each process: its current state, as stored with the analysis. A process with no analysis stays out of the totals and is listed apart, each with a link to Analyse.
- **Totals add up only what is known, and say so.** A process with an unknown hourly cost has an unknown monthly cost. The cost total adds the known ones and reads "4 of 6 processes with a known cost". The unknown row reads "Unknown", gives the reason and links to the process settings. An unknown is never drawn or added as zero.
- **The band shows when this browser has at least one process.** With none, Home stays as RS-106 defines it: three ways to start.
- **This browser's processes.** On the public demo, a process belongs to the browser that created it, through an anonymous cookie (ADR 0019). The overview, the process list on Home and the sidebar show only those. A process of another visitor still opens from its link, so the demo banner says that anything entered is visible to anyone with its link.
- **The API computes every figure**, including the totals, the count of known costs and each process's share of the known cost, which sets the length of its bar (ADR 0001, hard rule 7). The bars are SVG drawn from API values, as PDR 003 allows.

## Success criteria

- **The 30-second test.** Someone who returns to Home with a few analysed processes says, within 30 seconds and without help, how many hours and how much money a month their processes consume, and which one weighs most. Checked in the usability session of the design brief.
- Nobody reads a partial cost total as complete, or an unknown row as zero, in the same session.
- On the public demo, two browsers that create processes each see only their own on Home and in the sidebar, and a link to either process opens in both.

## Non-goals

- Savings, payback or ROI added up across processes. The question here is the baseline; the business case stays per analysis (PDR 003).
- Trends over time or comparisons between analyses.
- The processes of other visitors, or an aggregate of the whole instance.
- Privacy per process: a process stays readable by anyone with its id. Accounts and sign-in stay out of scope (PDR 001).

## Consequences

- What a demo visitor sees changes: the process list stops showing other visitors' processes.
- Four backlog items in B18 under RU-02: the visitor cookie (RS-110), the portfolio summary in the domain (RS-111), its endpoint (RS-112) and the band on Home (RS-113).
- `docs/design/` gains the discovery and the wireframes of the band before any code, as ADR 0013 asks for new screens.
