# ADR 0014: Keep the look of the vanilla client

**Status:** accepted · 2026-10-16 · amends the navigation and themes of ADR 0013

## Context

ADR 0013 chose a top bar with breadcrumbs instead of the sidebar of `web/`, and light and dark themes from the start. The first screens built that way (RS-73), with plain Tailwind and no tokens, looked flat next to the vanilla client. The Product Owner asked to keep the essence and the colours of `web/`: the dark navy surfaces, the blue accent, the cards with large radii and the sidebar with every process one click away.

## Decision

**Navigation.** The sidebar of `web/` comes back: brand, "+ New process" across its width, the process list with the current process marked (`aria-current="page"`), and the deterministic-first note at its foot. On narrow screens it folds above the page and the list scrolls sideways. Breadcrumbs and the process switcher of ADR 0013 are dropped.

**Themes.** The dark theme ships first, with the exact values of `web/styles.css` in `frontend/src/styles/tokens.css`, written in OKLCH. One value changes: the input border moves from `#33445e` to `#56698a`, because the original reached 1.9:1 against the input and WCAG 1.4.11 asks 3:1. The light theme and its toggle, as ADR 0013 decided them, come in a later item. They redefine the semantic layer only.

**Tokens.** The colours that `web/styles.css` wrote outside its variables (labels, input fields, table heads, toast) become tokens too. The default Tailwind palette is switched off, so only semantic tokens exist as utilities, and `src/styles/tokens.test.ts` fails on any colour literal or palette class outside `tokens.css`.

**Home.** The home page keeps the layout of `web/`: eyebrow, the two-line promise, the demo panel, then the creation form beside the process table. `/processes/new` stays for the sidebar button.

## Consequences

- During the migration, both clients look like the same product, and visitors see no change of identity when `/app` replaces `/ui/`.
- The sidebar takes 268 px from the results panels. They stack into one column below 1280 px wide, as in `web/`.
- Visitors in bright light wait for the light theme. The semantic layer is already split from the palette, so that item touches `tokens.css` and a toggle, and no component.
- Every colour decision now lives in one file, and the scan test keeps it there.

## Alternatives rejected

| Option | Why not |
|---|---|
| Top bar with the same colours | Keeps ADR 0013, but loses the one-click process list that the Product Owner asked to keep |
| Both themes now | Doubles the contrast work while the screens are still settling. The token split makes the light theme a contained change later |
| Copying `web/styles.css` as a global stylesheet | Fast, but brings back hard-coded colours and class names that Tailwind and the tokens replace |
