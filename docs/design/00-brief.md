# 00 Design brief

What the Next.js client (block B12) should look and feel like, how good is good enough, and what is left out on purpose. Every later document in `docs/design/` is judged against this one. The technical decisions behind it are in ADR 0013.

## Goal

A client that a demo visitor understands in ten seconds and an operations lead trusts with a budget decision. The design shows the core idea of the product: code computes every number, the AI only interprets, and the screen always says which is which.

## Audience

| Role | Optimise for | Where |
|---|---|---|
| Demo visitor | First impression and the shortest path from a demo to a blueprint | Home and the demo path |
| Operations lead | Clarity and efficiency with real data, up to a dozen steps | Steps editor, Analyse, Results |

When the two conflict, the home page and the demo path favour the visitor, and the working screens favour the operations lead.

## Decisions

| Topic | Decision |
|---|---|
| Personality | Sober and technical: neutral base, one accent, type and spacing doing the work |
| Brand | Evolves `web/`: accent `#8ab4ff` and the dark navy base, moved to OKLCH scales, plus a light theme |
| Themes | Dark first, with the exact palette of `web/` (ADR 0014). Light comes later, following the system by default, with a System, Light and Dark toggle stored in a cookie and rendered on the server |
| Language | English, sentence case |
| Navigation | The sidebar of `web/`: brand, "+ New process" and every process one click away, the current one marked (ADR 0014) |
| Type | Inter from a versioned package, tabular figures for numbers |
| Density | Medium, rows of about 44 px |
| Figures | Numbers, meters, horizontal bars and SVG charts drawn from API values and series, no chart library (SVG charts from PDR 003) |
| Tools | Penpot for wireframes and high fidelity, Claude Design for alternatives and the design system catalogue |

## Quality bar

### Every screen

- [ ] Designed at 1280 px and at 375 px.
- [ ] Every state drawn: normal, empty, loading (skeleton the size of the real content), error with a retry, and partial.
- [ ] One primary action per view, and it is obvious.
- [ ] Only tokens: 4 px spacing grid, the type scale, one accent. Status colours appear only for status.
- [ ] Figures use tabular digits, carry their unit, and sit right-aligned in tables.
- [ ] "Unknown" has its own style and never reads as zero.
- [ ] Contrast meets WCAG 2.2 AA in both themes, focus is visible, and touch targets are at least 44 by 44 px.
- [ ] Buttons say what happens ("Load and open", "Run analysis", "Save override").

### Every component

- [ ] States: default, hover, focus-visible, active, disabled and loading, where they apply.
- [ ] Works with the keyboard alone, with a visible accessible name.
- [ ] Does not rely on colour alone: text or an icon carries the meaning too.

### The process

- [ ] Each decision names the principle behind it, as the home page example in `02-ia-wireframes.md` does.
- [ ] Each screen gets a design critique before high fidelity.
- [ ] A usability session with three people, on a Penpot prototype of the critical paths. Findings change the screens not yet built, and become backlog proposals for the ones already built.

## Signature 1: the language of trust

The authority order of ADR 0001 (system facts, then user-confirmed facts, then LLM suggestions) becomes visible. Each level has an icon, a label and a style, never colour alone.

| Level | API data | Treatment |
|---|---|---|
| Computed by the rules | `final_source` `RULES`, every metric and score | Plain text. Source badge "Rules" |
| Your assumption | Implementation cost, tooling cost, expected reduction per step | Label "Your assumption", shown next to the figures that depend on it |
| AI suggestion | `ai_suggestion`, `final_source` `AI` | Badge "AI" in a reserved secondary tone, inside a dashed container. **Never applied to a number** |
| Human override | `final_source` `HUMAN`, `override` | Badge "Override", with the reason visible and the original value kept, de-emphasised |
| Unknown | `null` figures | The word "Unknown" in muted text, with an accessible tooltip that says why ("Hourly cost not set") |

Components: `SourceBadge`, `UnknownValue`, `ProvenanceBar` (rules version, prompt version, LLM status) and `AssumptionNote`.

**Test:** on any Results screen, someone who has never seen the product can point at a figure and say whether the rules, their own input or the AI produced it.

## Signature 2: waiting for the LLM

`POST /processes/{id}/analyses` answers once, with no progress events, and with the LLM it can take up to about 200 seconds. The design stays honest about that.

- **No fake progress bar.** An indeterminate indicator, the elapsed time, and one sentence: "Rules and AI analysis in progress. With the AI this can take up to about 3 minutes." Elapsed time is interface state, not a metric.
- **Screen readers.** A polite live region announces the start, the end and at most one reminder every 30 seconds, never every second.
- **Without the LLM**, the run is fast, and the button only shows a pending state.

| Outcome | What the user sees |
|---|---|
| `llm.status` `ok` | Results, with a toast |
| `llm.status` `unavailable` | Results, with a clear note that the deterministic results are complete. The daily quota (`error_kind` `daily_quota`) gets its own wording |
| Network or server error | The form keeps every value, with the error and a retry |

**To verify before designing the "leave this page" option:** whether the server still saves the analysis when the browser disconnects. Only then may the screen say "You can leave; it will appear in History".

**Test:** someone who starts an analysis with the LLM never asks "is it stuck?" during the wait.

## Out of scope

Animations longer than 200 ms, illustrations, chart libraries, translations, guided tours, a command palette and Storybook. Each one can come back as a backlog item with its own reason.

## Schedule

About ten hours of design a week. Design runs one screen ahead of code (ADR 0013), so each story waits only for its own screen.

| Week | Design | Code |
|---|---|---|
| 1 | This brief, the Steps wireframe, the first draft of `03-foundations.md` | RS-69, RS-70 |
| 2 | Foundations approved, Home in high fidelity, wireframes for Analyse and Results, the comparative heuristic evaluation | RS-71, RS-72, tokens |
| 3 | Steps and Results in high fidelity, with the Claude Design comparison, and `04-components.md` | RS-73 Home |
| 4 | Blueprint and History, the Penpot prototype and the usability sessions in `05-usability.md` | RS-74 Steps |
