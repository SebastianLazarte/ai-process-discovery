# 01 Discovery

First step of the design process in ADR 0013: who uses the client, what they need to get done, and what the current client (`web/`) already shows. The next documents build on this one.

## Roles and their jobs

From PDR 002. Each job reads "when ..., I want to ..., so I can ...".

| Role | Main job | What success looks like |
|---|---|---|
| Operations lead | When I own a process that eats hours, I want to see which steps are worth automating and how, so I can defend a budget with numbers | Can explain where every figure comes from, and which parts came from the rules and which from the AI |
| Demo visitor | When I review this project, I want to try it end to end in a few minutes, so I can judge the engineering without installing anything | Reaches a business case and a blueprint from a demo without reading docs |
| Maintainer | When the demo is public, I want visitors warned and their data kept short-lived, so I can run it safely | The public demo banner shows on every page |

**Design hypotheses** (to check in the usability sessions, not backlog items):

- A demo visitor reaches the results of a demo analysis in under three minutes and four clicks.
- An operations lead can tell rules output from AI output on every step without help.
- Nobody reads an unknown figure as zero.

## Objects

The client shows six objects. Everything on screen belongs to one of them.

| Object | Key content | Changed by the user |
|---|---|---|
| Process | name, owner, description, executions per month, hourly cost, version | Yes |
| Step | position, name, role, minutes, occurrence and exception rates, five levels (repetitiveness, rule clarity, criticality, input type, integration), tools, three flags (judgement, approval, sensitive data) | Yes, and reorder |
| Analysis | provenance (id, date, process version, rules version, LLM status, prompt version), current state, four panels | Created, never edited |
| Step assessment | rules method and score factors, AI suggestion, final method, human control and source | Through an override |
| Override | new method or control, required reason, original values kept | Created |
| Blueprint | eight sections derived from an analysis, Markdown download | Read only |

## Functional scope

What the new client must let people do, taken from the current client. The table lists capabilities, not layouts: the new screens are sketched from a blank page in `02-ia-wireframes.md`, without opening `web/` first, so the old layout does not anchor the new one.

| Current route | Purpose | Content to show | Actions | Backlog |
|---|---|---|---|---|
| `#/processes` | Start here | Hero, demo cards, new process form, process table | Load demo, create process | RS-73 |
| `#/processes/{id}` (Steps) | Describe the process | Header with tabs, four metrics, step list, process settings | Add, edit (dialog), move up or down, delete step; save or delete process | RS-73, RS-74, RS-91 |
| `#/processes/{id}/analyse` | Set assumptions and run | Implementation and tooling cost, a time reduction slider per step, LLM option, sensitive data gate | Run analysis | RS-75 |
| `#/analyses/{id}` (Results) | Read the analysis | Provenance, current state, four panels (suitability, impact, risk, controls), expandable step assessments | Override a step | RS-92, RS-76 |
| `#/analyses/{id}/blueprint` | Take the result away | Eight numbered sections | Download `.md` | RS-94 |
| `#/processes/{id}/history` | Compare runs | Table of immutable analyses | Open one | RS-93 |

Shared across pages: sidebar with the process list, public demo banner, toast (`role=status`), modal dialog for the step form, skip link, field errors from 422 answers.

## Critical paths

### A. Demo to blueprint (demo visitor)

```mermaid
flowchart LR
  A[Processes] -->|Load demo| B[Steps]
  B -->|Analyse tab| C[Analyse]
  C -->|Run analysis| D[Results]
  D -->|Blueprint tab| E[Blueprint]
  E -->|Download .md| F((File))
```

### B. Describe a process (operations lead)

```mermaid
flowchart LR
  A[Processes] -->|Create process| B[Steps, empty]
  B -->|Add step| C{{Step dialog}}
  C -->|Save| B
  B -->|Edit, move, delete| B
  B -->|Analyse tab| D[Analyse]
```

### C. Disagree with a recommendation (operations lead)

```mermaid
flowchart LR
  A[Results] -->|Open a step| B[Rules and AI columns]
  B -->|Override form| C{Reason given?}
  C -->|No| B
  C -->|Yes| D[Saved, original kept]
  D --> E[Blueprint reflects it]
```

## Constraints the design must keep

These come from ADRs and hard rules, so no layout may break them.

1. **The client never computes a figure** (ADR 0001, hard rule 7). The design shows numbers as the API returns them, formatted by one module. No totals, averages or charts derived in the browser.
2. **Unknown is never zero.** A missing hourly cost leaves cost, savings, payback and ROI as "unknown", and that must look different from a value.
3. **Four panels, never one score** (RS-53). Suitability, impact, risk and controls stay separate. No combined grade, traffic light or ranking across them.
4. **Authority is visible.** System facts, user-confirmed values and LLM suggestions must be distinguishable at a glance, and so must an override from the original.
5. **The LLM can raise a control, never lower one.** The UI must not offer an action that suggests otherwise.
6. **Sensitive data gate** (RS-54). With the LLM on and sensitive steps present, running stays disabled until the user confirms.
7. **Public demo banner** on every page while `public_demo` is true.
8. **Accessibility target** of ADR 0013: WCAG 2.2 AA, keyboard, visible focus, 375 px.

## Next

`02-ia-wireframes.md` sketches each screen from this document alone, starting with a worked example of the home page. The heuristic evaluation comes after the sketches and compares the old client with the new wireframes.

## Open questions for the Product Owner

- Should History stay a tab, or move to a panel on Results?
- Is mobile (375 px) a full-use target for every page, or read-only for Results and Blueprint?

## Analysis dashboard (B15, B16)

Added with PDR 003, for the first new screen area after the parity screens. It follows the same method as the rest of this document.

### Job

| Role | Main job | What success looks like |
|---|---|---|
| Operations lead | When I take an automation case to whoever approves the budget, I want to see how much we save and when the investment comes back, so I can defend it in one sentence | Answers both questions from Results in 30 seconds, and can say which inputs the answer depends on |

**Design hypotheses** (to check in the usability session):

- Someone who opens a demo analysis for the first time says the monthly saving and the payback month within 30 seconds.
- Nobody reads a patterned, unknown segment of a chart as zero.
- In B16, people understand that moving a control changes nothing stored until they save the scenario.

### Objects

| Object | Key content | Changed by the user |
|---|---|---|
| Analysis (B15) | Gains the cost after automation, the waterfall segments and the 12 points of the payback curve, all from the API | Created, never edited |
| Scenario (B16) | A business case recomputed from another expected reduction per step and another hourly cost, held only in the page | Yes, until saved as a new analysis |

### Critical paths

#### D. Defend the investment (operations lead, B15)

```mermaid
flowchart LR
  A[Results] -->|Read the band| B{Figures known?}
  B -->|Yes| C[Saving and payback month]
  B -->|No| D[Note names the missing input]
  D -->|Link| E[Process settings or Analyse]
  E -->|Run analysis| A
  C -->|Print| F((PDF))
```

#### E. Try another assumption (operations lead, B16)

```mermaid
flowchart LR
  A[Results] -->|Change a reduction or the hourly cost| B[Band redraws from the API]
  B -->|Reset| A
  B -->|Save as new analysis| C[New analysis in History]
```

### Constraints the dashboard adds

9. **Series come from the API.** Every bar, segment and point is an API field. The client only scales a value to a length in pixels, as it does on a `<meter>`.
10. **Each chart has a data table** with the same figures, and no chart relies on colour alone: labels sit on the bars and lines, and unknown segments carry a pattern and the word "Unknown".
11. **Print has its own light palette.** Only the dark theme exists today (ADR 0014), and a dark page wastes toner and prints poorly.
