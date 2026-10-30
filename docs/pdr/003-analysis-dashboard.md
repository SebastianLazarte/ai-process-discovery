# PDR 003: Analysis dashboard and what-if scenarios

**Status:** proposed · 2026-10-26 · amends the design brief (figures)

## Problem

An operations lead has to defend an automation budget to whoever approves it. Results shows the business case as six separate figures: hours freed, gross and net savings, implementation cost, payback and ROI at 12 months. The two questions a budget holder asks first, "how much do we save" and "when do we get the money back", need someone to read several cards and do the arithmetic in their head. Changing an assumption to answer "and if we only save half of that?" means going back to Analyse and running a new analysis.

## Decision

Two releases, after B14 (guided capture) closes. Both serve the operations lead (PDR 002) and the decision "is this investment worth it".

### B15: analysis dashboard (read only)

- A band at the top of Results, above the four panels, with two charts:
  - **Cost waterfall:** current monthly cost, minus gross savings, plus tooling cost, ending at the monthly cost after automation. The gap between the first and the last bar is the net monthly saving.
  - **Payback curve:** cumulative net savings month by month over a fixed 12-month horizon, against the implementation cost as a flat line. The crossing is the payback month. The horizon matches the ROI at 12 months that Results already shows, so the curve and the figure tell the same story.
- **Partial charts.** When a figure is unknown, the chart draws the known parts and marks the unknown ones with a pattern and a note that names the missing input and links to where it is set. An unknown is never drawn as zero.
- **Every chart has a data table**, available to screen readers and on demand on screen, with the same figures as the chart.
- **Full reading at 375 px:** the charts adapt to the width, and nothing on the band is desktop only.
- **Printable Results.** A print stylesheet so the browser can save Results as a PDF: provenance, the dashboard band and the four panels, without navigation, buttons or forms. No new dependency.

### B16: what-if scenarios

- On Results, the operations lead can change the **expected reduction per step** and the **hourly cost**. Each change asks the API to recompute the business case without saving anything, and the dashboard redraws from the answer.
- A scenario can be **saved as a new analysis**: immutable, listed in History like any other, with its own provenance. The LLM is not called again.
- Implementation cost and monthly tooling cost stay fixed in B16. They can come back as a backlog item.

### Figures and drawing

- **The API sends every figure and every series the charts need**, in `Decimal` and computed in `domain/` (ADR 0001, hard rule 7). That includes the cost after automation, the start and end of each waterfall segment, and the 12 points of the payback curve. The client never adds, subtracts or accumulates.
- **Scaling a value to a length in pixels is drawing**, the same as placing a value on a `<meter>`. The client may do it.
- **Charts are hand-drawn SVG components**, with sizes in SVG attributes and colours from the design tokens, so they work under the CSP that blocks `style=` (RS-72). The brief's "no chart library" stays: a library would bring a dependency, an ADR and inline styles.
- The brief's "Figures" decision changes from "numbers, meters and horizontal CSS bars" to "numbers, meters, horizontal bars and SVG charts drawn from API values and series".

## Success criteria

- **The 30-second test.** Someone who opens a demo analysis can say, within 30 seconds and without help, how much the process saves per month and in which month it pays back. Checked in the usability session of the design brief, with three people.
- Nobody reads an unknown figure on a chart as zero, in the same session.
- On the dashboard, every figure can be traced to an API field, and no chart computes a value in the browser (checked in code review and by a component test per chart).
- In B16, a saved scenario appears in History, and opening it shows the same figures the simulation showed.

## Non-goals

- A portfolio dashboard across processes, or trends across analyses in History. Each can come back as its own record.
- Simulating implementation cost or tooling cost (B16 can widen later).
- Charts for suitability, risk or human controls. The band is about the business case only, and it never combines suitability, impact, risk and controls into one score (RS-53).
- Export to PDF on the server, images of charts, or adding the charts to `blueprint.md`.
- A chart library.

## Open questions, to settle while refining B16

- **Hourly cost lives on the process**, not on the analysis assumptions. A saved scenario with another hourly cost either creates a new process version or moves the hourly cost into the assumptions of the analysis. The choice touches the domain and the contract and may need an ADR.
- **What a saved scenario keeps from its source analysis.** The AI suggestions do not depend on economic values (the LLM never sees them), so they could be carried over with a note, or the new analysis could carry no AI part and show `not_requested`.
- **Cost on the public demo.** The scenario endpoint runs only the rules, with no LLM call, but each slider change is a request. It needs a rate limit in line with RU-10, and the client should wait for the user to stop moving before it asks.

## Consequences

- Two releases, B15 "Analysis dashboard" and B16 "What-if scenarios", with their milestones in `scripts/bootstrap_github.py`.
- One new epic, approved by the Product Owner on 2026-10-26. It enters `docs/requirements.toml` with the first backlog items of B15, because every epic must have at least one item (`tests/unit/test_requirements_file.py`):

  ```toml
  [user_requirements.RU-15]
  name = "Business case at a glance"
  as_a = "operations lead"
  i_want = "to see how the savings build up against the investment, and to try other assumptions before I commit to one"
  so_that = "I can tell whoever approves the budget how much we save and when the money comes back"
  ```
- The business case domain gains the cost after automation, the waterfall segments and the payback series, each with unit and property-based tests under the standard of ADR 0012.
- `docs/design/` gains the discovery and the wireframes of the band before any code, as ADR 0013 asks for new screens.
