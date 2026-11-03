# ADR 0018: Graphite, a modern take on the vanilla look

**Status:** accepted · 2026-11-03 · amends the navigation and the surfaces of ADR 0014

## Context

ADR 0014 kept the look of the vanilla client: its dark navy palette, the blue accent, cards with large radii and a sidebar with every process one click away. With 2.0.0 live, the Product Owner judged the interface dated. A review of the live demo found why:

- Every element weighs the same. Cards with borders sit inside panels with borders, and only text size sets the hierarchy.
- The main action of a view hardly shows. "Load and open" is a grey outlined button, and the only strong button on the page is "+ New process" in the sidebar.
- Prose leads and figures follow. On Results the provenance line comes before the business case, and the strongest figure is the suitability score.
- The demo banner is heavy, the sidebar is empty on a first visit, and there are no icons or empty states.

Three visual directions were drawn as high-fidelity mockups of Home and Results with the data of a demo (a light report style, this one, and a soft light workspace). The Product Owner chose this one, Graphite, on 2026-11-03.

## Decision

Graphite keeps the identity of ADR 0014, the dark theme and the accent `#8AB4FF`, and changes how the screens are built:

- **Surfaces.** Depth comes from elevation: the page ground, a raised surface and a higher one, each a token. Borders stay only where they separate content inside a surface, such as table rows. No card sits inside a bordered panel.
- **One primary action per view**, a filled button in the accent. Secondary actions are filled with a raised surface, and tertiary ones are text.
- **The answer first.** Results opens on a band with the net saving per month and the payback, from API figures. Provenance (rules version, LLM status, prompt version, process version) moves into small monospaced chips beside it, still on screen and never hidden.
- **Navigation in two forms.** Home and the process list keep the full sidebar of ADR 0014. Inside a process the sidebar becomes a rail of icons with accessible names, so Results gains width; every process stays one click away through the rail.
- **Process tabs** are a segmented control. The demo banner becomes a slim line with a status dot and keeps its full text.
- **Trust badges** follow the design brief: Rules plain, AI dashed in a reserved tone and never on a number, Override with its reason, Required for human controls.
- **Icons** are inline SVG components of our own, drawn with the stroke of the type. No icon package.

The tokens and their contrast rules of ADR 0014 stay: every colour lives in `tokens.css`, text reaches 4.5:1 and control borders and focus 3:1. The light theme of ADR 0013 is still later work and redefines only the semantic layer.

The mockups are the reference for the screens, together with the criteria of RS-104 to RS-109 (block B17). B17 comes before the dashboard of PDR 003 (B15), so its charts are drawn on Graphite from the start.

## Consequences

- Every screen changes, though not its content or its behaviour. The e2e walkthroughs and the axe pass of RS-78 are the safety net for the restyle.
- Results gains about 200 px of width inside a process, which the four panels and the B15 band use.
- The rail hides the process names inside a process. The process name stays in the page header, and the full list is one click away.
- No new dependency: icons and charts are our own SVG.

## Alternatives rejected

| Option | Why not |
|---|---|
| A light, report-like style with top navigation | A clean break, but it drops the identity and the sidebar that ADR 0014 kept on purpose, and the light theme would come before the dark one is finished |
| A soft light workspace with a product-app feel | Friendly, but generic, and it also starts from the light theme |
| An icon package such as Lucide | Saves drawing a dozen icons, at the cost of a dependency and an ADR for something small |
| Keeping ADR 0014 as it is | The review found the problems are structural, so new colours alone would not fix them |
