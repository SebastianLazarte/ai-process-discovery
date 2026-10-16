# ADR 0013: Design system and design-to-code workflow

**Status:** proposed · 2026-10-16 · amends the dependencies of ADR 0009

## Context

ADR 0009 chose the frontend stack (Next.js, Tailwind, shadcn/ui) and left the visual layer open: no tokens, no themes, no accessibility target beyond "accessible components", no font strategy and no design tool. The only design source today is `web/styles.css`: a dark palette of CSS variables, many hard-coded colours outside them, and no spacing or type scale.

The new client is a portfolio piece, so its design process has to be as legible as its code. The maintainer also wants to learn UI and UX on the way, with tools that need no paid licence.

## Decision

**Process.** Each screen goes through discovery, information architecture and low-fidelity wireframes, visual foundations, high-fidelity design and then code. The artefacts live in `docs/design/`, numbered in that order. Design runs one screen ahead of code: a story waits only for the approved spec of its own screen and for the foundations (tokens and primitives), never for the whole set. The order follows the backlog: Home (RS-73), then Steps (RS-74), Analyse and Results (RS-75), Blueprint and History (RS-76).

**Tokens in code are the source of truth.** `frontend/src/styles/tokens.css` holds every design decision as CSS custom properties in three layers:

| Layer | Example | Who uses it |
|---|---|---|
| Primitive | `--blue-400`, `--space-4`, `--text-lg` | Only the semantic layer |
| Semantic | `--surface`, `--text-muted`, `--accent`, `--status-warn-fg` | Components and Tailwind utilities |
| Component | `--meter-track` | One component, only when no semantic token fits |

- Colours are written in OKLCH, so lightness steps are even and contrast is predictable.
- Spacing follows a 4 px grid, and type follows a modular scale.
- Tailwind v4 exposes the semantic layer through `@theme`, and the shadcn variables (`--background`, `--primary` and so on) point to semantic tokens.
- Components never use a raw colour literal. A Vitest check scans `src/components/` for hex, `rgb(` and `oklch(` and fails when it finds one.

**Themes.** Light and dark follow `prefers-color-scheme` by default. A toggle in the top bar offers System, Light and Dark, and stores the choice in a `theme` cookie. The root layout reads that cookie on the server and renders `data-theme` on `<html>`, so the first paint already has the right theme, with no inline script and no change to the CSP nonce of ADR 0009. The cookie holds only that preference.

**Palette.** It evolves the identity of `web/styles.css`. In the dark theme, the key values of `web/` stay exactly the same, written in OKLCH: the background `#0b111b`, the accent `#8ab4ff` and the four status pairs (good, info, warn, bad). The scales are built around those anchors, and the light theme is derived from the same scales.

**Visual direction.** The brief is in `docs/design/00-brief.md`.

- Sober and technical: a neutral base, one accent, and type and spacing doing the work instead of decoration.
- English copy, in sentence case.
- Navigation through a top bar and breadcrumbs, with no sidebar, so the four results panels get the full width. The process segment of the breadcrumb is a menu button that lists the processes, so switching process takes one click and a choice, also from the keyboard.
- Medium density: table and list rows of about 44 px, which are also valid touch targets.
- Figures come as numbers, meters and horizontal bars drawn in CSS from the values the API returns. There is no chart library, so nothing on screen can look as if the client computed it. Each bar prints its exact figure and has an accessible name, and the detail of each step lives in its expandable assessment, so no information depends on hover.

**Accessibility target: WCAG 2.2 AA.**

- Text contrast is at least 4.5:1, and UI components and focus indicators at least 3:1, in both themes.
- Everything works with the keyboard, focus is always visible, and a skip link is present.
- Layouts work from 375 px wide.
- Motion respects `prefers-reduced-motion`.
- Status is never carried by colour alone: every badge and meter also has text.

**Checks.**

| Check | Where |
|---|---|
| `eslint-plugin-jsx-a11y`, strict preset | `frontend` job, through lint |
| Component tests query by accessible role and name | `frontend` job |
| `@axe-core/playwright` fails on serious or critical violations on every page of the walkthroughs | `e2e` job |
| The walkthroughs run twice, at 1280 px and at 375 px (two Playwright projects) | `e2e` job |
| A keyboard-only walkthrough of the three critical paths: Tab, Enter, Space and Escape, no pointer, and it checks that the focused element shows a visible outline at every step | `e2e` job |
| A screen reader pass with NVDA (free) over the three critical paths | Once per release, recorded in the release pull request |

**Fonts.** Inter comes from the `@fontsource-variable/inter` package and loads through `next/font/local`. The font is pinned in the lockfile like any other package, the build fetches nothing outside the package registry, and the app serves it from its own origin, so the CSP `font-src 'self'` holds. Figures use `font-variant-numeric: tabular-nums`, so the digits line up in columns.

**Design tools.** These live outside the repository, need no paid licence, and add no dependency:

| Tool | Use |
|---|---|
| Penpot | Wireframes, flows, components and a copy of the tokens in its native token format (W3C DTCG), read through its MCP server |
| Claude Design | High-fidelity exploration from the wireframes, and handoff to code |

What the tools hold mirrors `tokens.css`. When they disagree, the code wins, and the tool is updated. When a screen is approved, its frames are exported as PNG to `docs/design/img/`, under the 500 kB limit of the pre-commit hook, and the Penpot file export (`.penpot`) is attached to the pull request that approves it. Everything approved lives in the repository or in its pull requests.

**Dependencies added to ADR 0009.**

| Package | Why |
|---|---|
| `@fontsource-variable/inter` | Inter as a versioned package, so the build does not depend on Google Fonts |
| `@tailwindcss/postcss`, `postcss` (dev) | The integration that Tailwind v4 needs to run inside the Next build |
| `eslint-config-next` (dev) | The Next presets (`core-web-vitals`, `typescript`) for the flat ESLint config, since Next 16 removed `next lint` |
| `jsdom`, `@testing-library/dom` (dev) | The DOM environment for Vitest and the peer dependency of `@testing-library/react` |
| `@types/react`, `@types/react-dom`, `@types/node` (dev) | Type definitions for strict TypeScript |
| `@axe-core/playwright` (dev) | Automated WCAG checks in the end-to-end walkthroughs |
| `eslint-plugin-jsx-a11y` (dev) | Static accessibility rules for JSX. `eslint-config-next` already pulls it in, and it is now declared so the strict preset is pinned |

## Consequences

- RS-73 to RS-76 each get an approved screen spec before code, and review checks a pull request against the states listed in that spec. Since design runs one screen ahead, the first screen component waits only for the Home spec and the foundations, about two weeks, and RS-69 to RS-72 can start at once.
- Colour, spacing and type live in one file, and the literal scan fails the build when a component bypasses it. That includes the shadcn components copied into the repo.
- An accessibility regression that a tool can detect fails `frontend` or `e2e` before merge, at both widths and with the keyboard alone. The only manual check left is the screen reader pass, once per release instead of in every pull request.
- In the dark theme, the background, the accent and the status colours keep the exact values of `web/`, so the two clients look like the same product throughout the migration.
- The build fetches the font from the package registry, as it already does for every other package, and the font version moves only through the lockfile and the update policy of ADR 0010.
- The packages in the table above follow the update policy of ADR 0010. Only `@fontsource-variable/inter` reaches the served assets, and only as a font file. The rest are development tools.
- Design files are drafted in Penpot and Claude Design, and everything approved is exported to the repository or attached to its pull request. Losing an account loses only work in progress.
- Bars print their exact figure and need no hover, so they read the same with a mouse, on a touch screen, with the keyboard and with a screen reader.
- Visitors keep their system theme by default and can override it with one control. Switching between processes takes one click and a choice from the breadcrumb menu.

## Alternatives rejected

| Option | Why not |
|---|---|
| Figma | The free plan allows only a handful of MCP calls a month, and Dev Mode needs a paid seat |
| Penpot or Claude Design as the source of truth | Tokens would need an export step on every change, and the reviewed pull request would no longer hold the decision |
| Style Dictionary or another token build | A dependency and a build step for about sixty tokens that fit in one CSS file |
| Storybook | A large dependency tree for about fifteen components. Component tests cover the states, and Claude Design shows the catalogue. Worth revisiting if the component count grows |
| Theme toggle stored in `localStorage` | Needs an inline script before paint, which conflicts with the nonce CSP, or the page flashes the wrong theme. The cookie read on the server avoids both |
| Inter through `next/font/google` | The build would depend on Google Fonts being reachable, a host outside the lockfile and the update policy |
| Designing every screen before any code | About four weeks before the first component, and specs that age while they wait. One screen ahead keeps each spec close to its story |
| Dark theme only, as in `web/` | Fails visitors who read in bright light, and a single theme hides contrast mistakes |
| A chart library such as Recharts | A dependency and its accessibility work for figures that CSS bars show well, with the risk of charts that look computed in the browser |
| Sidebar with the process list, as in `web/` | Repeats the home list, takes about 240 px from the results panels, and turns into a drawer on mobile |
