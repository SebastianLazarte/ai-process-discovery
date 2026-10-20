# ADR 0015: The parity screens take the vanilla client as their spec

**Status:** accepted · 2026-10-19 · amends the design process of ADR 0013 (an approved spec before each screen)

## Context

ADR 0013 sends each screen of the Next.js client through discovery, wireframes, visual foundations and high-fidelity design before code, with an approved spec in `docs/design/` one screen ahead of its story. ADR 0014 then kept the look of `web/`: its sidebar, its cards and its exact dark palette as tokens.

On 2026-10-19 the Product Owner decided that the vanilla client at `/ui/` should leave the public demo as soon as possible, and that the demo must never look broken on the way. The Next.js client therefore has to reach parity with `web/` before it goes public (ADR 0016). The screens still missing are Steps (RS-74, RS-91), Analyse (RS-75), Results and overrides (RS-92, RS-76), History (RS-93) and Blueprint (RS-94). All of them already exist in `web/`, and ADR 0014 already fixed how they look. Wireframes and high-fidelity frames for them would take weeks and show a reviewer nothing that `web/` does not show today.

## Decision

**Spec.** RS-74, RS-91, RS-75, RS-92, RS-76, RS-93 and RS-94 take as their spec the behaviour and the look of the same screen in `web/` (ADR 0014), together with the refined criteria of each item in `docs/requirements.toml`. Where the two disagree, the criteria win. For example, a null figure shows `Unknown` (RS-92), although `web/format.js` prints `n/a` for some of them.

**No design gate for these items.** They get no Penpot wireframes, no high-fidelity frames and no new document in `docs/design/`. A story starts as soon as the shared client foundation it uses is merged.

**What stays from ADR 0013.** Tokens in `tokens.css` as the source of truth, WCAG 2.2 AA, the accessibility checks (lint, role queries, axe at 1280 and 375 px, the keyboard walkthrough), the fonts, and figures printed as numbers and CSS bars with no chart library. The amendments of ADR 0014 hold.

**Review.** Each pull request is compared with the same screen of `web/` and with the criteria of its item. Until the `e2e` job exists (RS-78), the pull request records a walkthrough of the new screen with `pnpm dev`, `uvicorn` and the fake LLM provider, next to the same path in `/ui/`. Every visible difference from `web/` is listed in the pull request and traced to a criterion, an accessibility fix or a rule of the new client (for example, the nonce CSP blocks inline `style` attributes).

**After parity.** New layouts, the light theme of ADR 0013 and any screen without a counterpart in `web/` follow the design process of ADR 0013, as their own items after 2.0.0.

## Consequences

- The seven items wait for no design work, so they can run in parallel once the shared foundation is in.
- Review has one concrete reference per screen. A reviewer can open both clients side by side and tell a regression from a choice.
- `web/` is the reference until RS-80 removes it. After that, the last 1.x tag keeps it.
- Weak spots of `web/` carry over unless a criterion or an accessibility rule fixes them. `web/` itself still takes no new features.
- ADR 0013 stays proposed. Its design process now applies to new screens only, and its other decisions are unchanged.

## Alternatives rejected

| Option | Why not |
|---|---|
| Wireframes and high-fidelity frames for every remaining screen, as ADR 0013 asks | Weeks before code for screens that already exist, while `/ui/` stays public |
| Redesign the screens during the migration | Mixes two changes in each pull request, so review cannot tell a regression from a design choice |
| Port `web/` code as it is | Brings back HTML strings, `h()` and hard-coded colours that React, the tokens and the CSP replace |

## How to revert

Restore the design gate of ADR 0013 for the items not yet merged: each one waits for its approved spec in `docs/design/`. Merged screens need no change.
