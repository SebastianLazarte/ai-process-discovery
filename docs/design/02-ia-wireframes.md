# 02 Information architecture and wireframes

Second step of the design process in ADR 0013. Each screen is sketched from `01-discovery.md` alone, in greyscale, before anyone opens the current client. Colour, type and spacing come later, in `03-foundations.md`, so the sketches are judged only on structure and content.

## Method, for every screen

1. **Who arrives, from where, wanting what.** One line per role.
2. **Content priority.** Rank everything the screen could show. The rank decides size and position, not the other way round.
3. **States.** Empty, loading, error, partial, and the normal case. A screen designed only for the normal case is half designed.
4. **Three alternatives.** Quick sketches of different structures, not variations of one. The first idea is rarely the best, and comparing three shows why.
5. **Choose and say why.** Name the principle behind each decision, so a reviewer can disagree with the reason and not only the result.
6. **Wireframe at 1280 px and 375 px.** Mobile is designed, not squeezed: decide what stacks, what hides and what changes form.
7. **Open questions.** What only a usability session can answer.

## Navigation

The current client has a sidebar that repeats the process list from the home page. This section compared it with a top bar and breadcrumbs, and the top bar was chosen first. ADR 0014 brought the sidebar back, so that the new client keeps the look of the vanilla one. The comparison stays below as a record of the trade-off.

| Option | For | Against |
|---|---|---|
| Sidebar with process list | Switch between processes in one click | Duplicates the home list, takes about 240 px from the four results panels, and has to collapse on mobile anyway |
| **Top bar and breadcrumbs** | Full width for content, the same pattern at every size, and the breadcrumb answers "where am I" | Solved: the process segment of the breadcrumb is a menu that lists the processes, so switching takes one click and a choice |

Breadcrumb inside a process: `Processes / Warranty claims from installers / Results`. The process tabs (Steps, Analyse, Results, Blueprint, History) stay below the page title.

**Principle: Jakob's law.** People spend most of their time on other sites, so a top bar with breadcrumbs is a pattern they already know.

## Worked example: Processes (home)

Backlog: RS-73. Route in the new client: `/` (`/app/` during the migration).

### 1. Who arrives

| Role | From | Wants |
|---|---|---|
| Demo visitor | A link on a CV or portfolio, first visit | Understand what this is in ten seconds, then try it without typing |
| Operations lead | A bookmark, returning | Open their process, or start a new one |

On the public demo, the process list also holds other visitors' processes. It is never truly empty, and it is never truly "yours".

### 2. Content priority

1. What the product does, in one sentence. Without it, nothing else makes sense.
2. The fastest way to try it: the three demos, each with its name and description from the API.
3. The existing processes.
4. Creating a new process. It needs five fields that only make sense once you know what a process is here.
5. Why the numbers can be trusted (rules compute, the AI interprets). It matters, but in one line, not a paragraph.

The public demo banner sits outside this ranking. It is a system message and always comes first.

### 3. States

| State | What shows |
|---|---|
| Normal | Banner, intro, demos, process list |
| No processes | The list area says "No processes yet. Load a demo or create one." with the New process button. Demos stay above |
| Loading | Skeleton rows the size of real rows, so the layout does not jump |
| Loading a demo | That card's button shows "Loading..." and is disabled; the other cards stay usable |
| API down | The intro still shows; the list and demo areas show the error with a Retry button |
| Not a public demo | No banner; everything else is the same |

### 4. Three alternatives

**A. Everything on one page.** Intro, demos, the creation form and the process table, all visible at once.
- For: no clicks to reach anything.
- Against: four blocks compete for attention, and the five-field form greets visitors who do not know yet what a process is.

**B. Two doors.** A large choice between "Try a demo" and "Map your own process", with the list below.
- For: a single, clear decision.
- Against: one more click to reach the demos, and two equal buttons make the user choose before they understand.

**C. Demo first, form on demand.** Intro, demos with one-click loading, then the list with a New process button that opens its own page.
- For: one obvious first action, and the form appears only when someone asks for it.
- Against: a returning operations lead scrolls past the demos to reach the list.

### 5. Choice: C

- **Hick's law.** The time to decide grows with the number of choices. C shows one kind of primary action above the fold: load a demo.
- **Progressive disclosure.** The creation form moves to `/processes/new`. It has a URL, the browser's Back button leaves it, and it works on mobile without a dialog over a dialog.
- **Product Goal.** PDR 002 makes the demo visitor the most frequent first-time user, so the first screen serves them.
- **Microcopy says what happens.** "Load demo" becomes "Load and open", because the button creates a copy and takes you to it.
- **Accepted cost.** The returning operations lead scrolls once. If the usability sessions show that hurts, the list can move above the demos when the visitor already has processes.

### 6. Wireframes

Desktop, 1280 px:

```text
+------------------------------------------------------------------------------+
| (!) Public demo v1.3.0. Anything you enter is visible to other visitors and  |
|     deleted periodically. Do not enter real or personal data.                |
+------------------------------------------------------------------------------+
| [logo] Process Discovery                  Processes        [ + New process ] |
+------------------------------------------------------------------------------+
|                                                                              |
|  Map a process. Get numbers you can defend.                            (h1)  |
|  Rules compute every hour and cost. The AI only interprets.          (lead)  |
|                                                                              |
|  Try a demo                                                            (h2)  |
|  +------------------------+ +------------------------+ +------------------+  |
|  | Order intake from      | | Warranty claims from   | | Zoning design    |  |
|  | distributors           | | installers             | | and quote        |  |
|  | A manufacturer of      | | A manufacturer of      | | Installers send  |  |
|  | zoned HVAC controls... | | zoned HVAC controls... | | the floor...     |  |
|  | [ Load and open    > ] | | [ Load and open    > ] | | [Load and open >]|  |
|  +------------------------+ +------------------------+ +------------------+  |
|                                                                              |
|  Processes                                              [ + New process ]    |
|  +------------------------------------------------------------------------+  |
|  | Name                      Owner     Runs/month  Steps  Version Updated |  |
|  |------------------------------------------------------------------------|  |
|  | Warranty claims from i... Service          180      7       v1  16 Oct |  |
|  | Order intake from dist... No owner         ...    ...      ...  16 Oct |  |
|  +------------------------------------------------------------------------+  |
+------------------------------------------------------------------------------+
```

Mobile, 375 px:

```text
+-----------------------------------+
| (!) Public demo v1.3.0. Anything  |
| you enter is visible to other     |
| visitors and deleted periodically.|
| Do not enter real or personal     |
| data.                             |
+-----------------------------------+
| [logo] Process Discovery  [+ New] |
+-----------------------------------+
| Map a process. Get numbers you    |
| can defend.                       |
| Rules compute every hour and      |
| cost. The AI only interprets.     |
|                                   |
| Try a demo                        |
| +-------------------------------+ |
| | Warranty claims from          | |
| | installers                    | |
| | A manufacturer of zoned...    | |
| | [ Load and open           > ] | |
| +-------------------------------+ |
| (two more cards, stacked)         |
|                                   |
| Processes                         |
| +-------------------------------+ |
| | Warranty claims from inst...  | |
| | Service . 7 steps . v1        | |
| | 180 runs/month . 16 Oct       | |
| +-------------------------------+ |
+-----------------------------------+
```

Mobile decisions:

- **No hamburger menu.** The top bar holds only two destinations, and hiding two links behind an icon costs a tap and hides them for nothing.
- **The table becomes a list of cards.** Six columns do not fit in 375 px. Each row becomes a card with the name on top and the facts below, and the whole card is the link.
- **The banner keeps its full text.** A shorter warning would change what visitors are told. It takes the first screen once, and the user can scroll past it.
- **Touch targets of at least 44 by 44 px** for every button and card (Fitts's law: small, distant targets are slow and error prone).

### 7. Open questions

- Do visitors understand that "Load and open" creates their own copy, which others can see?
- On mobile, does anyone scroll past the banner and the intro to reach the demos?

## Your turn: Steps editor

Apply the seven steps to the Steps page of a process (RS-74, RS-91), in Penpot, in greyscale, at 1280 and 375 px. It is the hardest screen of the client: a step has fifteen fields, and the page must show several steps at once.

Questions to help you with ranking and alternatives:

- Which three facts about a step does someone need to see in the list, and which only when editing?
- Edit in a dialog, in a side panel, inline in the list, or on its own page? Sketch at least three of these.
- How do you reorder steps with the keyboard and on a touch screen, without relying on drag and drop?
- What does the page look like with zero steps, with one, and with twelve?
- How do you show that "Exception rate" is unknown and not zero?

Write your result as a new section of this document, with the same seven headings as the worked example. I review it before you move on to the next screen.

Then, in order: Analyse (RS-75), Results (RS-92, RS-76), Blueprint (RS-94) and History (RS-93).

## Analysis dashboard on Results (B15)

Scope in PDR 003, discovery in the "Analysis dashboard" section of `01-discovery.md`. Results itself is a parity screen (ADR 0015); this section designs only the new band at its top. The what-if controls of B16 are sketched once B15 is refined, one screen ahead of code. The figures in the sketches are an example: a current cost of 6800.00 a month, gross savings of 4570.00, tooling of 150.00 and an implementation cost of 18000.00, so a net saving of 4420.00 a month and payback in month 4.1.

### 1. Who arrives

| Role | From | Wants |
|---|---|---|
| Operations lead | Analyse after a run, or History | The monthly saving and the payback month, in a form they can take to a meeting |
| Demo visitor | "Load and open" on a demo with preset assumptions (RS-89), which lands on Results | See in seconds what the product produces |

### 2. Content priority

1. The two answers: the net monthly saving and the payback month, with their units.
2. The payback curve: when the money comes back.
3. The cost waterfall: where the saving comes from.
4. What the answers depend on: the user's assumptions, and any missing input with a link to set it.
5. The same figures as tables, on demand.

The provenance bar stays above the band. It says which analysis this is, so it comes first.

### 3. States

| State | What shows |
|---|---|
| Normal | Both charts, with titles that state the answer ("Saves 4420.00 a month", "Pays back in month 4.1") |
| Hourly cost unknown | Current cost, savings and cost after automation are unknown: patterned bars with "Unknown". Tooling still shows. The curve draws only the investment line. Note: "Hourly cost not set", with a link to the process settings |
| Implementation cost unknown | The waterfall is complete. The curve draws only the savings line, with the title "Payback unknown". Note: "Implementation cost not set", with a link to Analyse |
| Never pays back | Net saving zero or negative: the curve stays flat or falls, with the title "Does not pay back: tooling costs as much as it saves or more". A warning note, never red bars |
| Pays back after month 12 | The crossing is off the chart: an arrow at the right edge, with the title "Pays back after month 12 (month 18.4)" |
| No implementation cost | An implementation cost of zero: the title "Pays back at once" |
| Steps without a reduction | The assumptions line repeats the existing note: they count as zero, because that is the user's input and the figure is known |
| Loading | A skeleton the size of the band, so the panels below do not jump |
| Print | Light palette, the tables printed under each chart, navigation, tabs, buttons and forms hidden, one A4 page as the target |

### 4. Three alternatives

**A. A band of two charts above the four panels.**
- For: the answer is the first thing on Results, where every analysis lands, demos included.
- Against: the net saving and the payback also appear in the Business impact panel below.

**B. The charts inside the Business impact panel.**
- For: no repeated figures, and Results keeps its structure.
- Against: the panel shares the first row with suitability, so the charts are half width at most and below the fold on a laptop.

**C. A tab of its own, "Business case".**
- For: room for the charts, and later for the what-if controls.
- Against: one more click, and a demo visitor who lands on Results never sees it.

For the payback curve, three forms were compared: **two lines** (cumulative savings and the investment), **one net position line** that starts below zero and crosses it, and **monthly bars**.

### 5. Choice: A, with a two-line curve and a horizontal waterfall

- **Answer first (inverted pyramid).** The Product Owner put the band at the top. The 30-second test starts where the analysis lands, and A is the only option that shows the answer there without a click.
- **Titles state the answer.** Each chart title is the conclusion, as in the action titles of a consulting deck, and the chart is the evidence. Someone who reads only the titles passes the 30-second test.
- **Two lines degrade gracefully.** With the implementation cost unknown, the savings line still draws and only the investment line is missing. A net position line cannot start without the investment, so it would show nothing. The crossing reads as "the money is back", with no negative axis to explain.
- **A horizontal waterfall.** The labels fit at 375 px without rotation, so the form is the same at both widths (consistency), and it extends the horizontal bars the brief already allows.
- **Status colours only for status** (brief). Bars are neutral and savings use the accent. "Never pays back" is a warning note, so a red bar never reads as an error of the product.
- **Accepted cost.** The band repeats two figures of the Business impact panel. The band answers and the panel details. The usability session decides whether the panel keeps them.

### 6. Wireframes

The sidebar is the same as on every page and is left out of the sketches.

Desktop, 1280 px:

```text
+------------------------------------------------------------------------------+
| Results . Analysis 3f2a1c, process v2, rules 1.4.0, LLM ok     (provenance)  |
+------------------------------------------------------------------------------+
| Business case                                                   [ Print ]    |
| From your assumptions: implementation 18000.00, tooling 150.00 a month,      |
| a reduction on 5 of 7 steps.                       [ Change on Analyse ]     |
|                                                                              |
| +-----------------------------------+ +------------------------------------+ |
| | Saves 4420.00 a month             | | Pays back in month 4.1             | |
| |                                   | |                                    | |
| | Current cost      ##########  6800| | 53040 |                        ..o | |
| | Gross savings        <======  4570| |       |                  ...''     | |
| | Tooling              =>        150| |       |            ...''           | |
| | After automation  ####        2380| | 18000 |- - -x- - - - - - - - - - - | |
| |                                   | |       |  ..' investment            | |
| | Net saving, the gap: 4420.00      | |     0 +--+--+--+--+--+--+--+--+--  | |
| |                                   | |       0  1  2  3  4  ...       12  | |
| | [ Show as a table ]               | | [ Show as a table ]                | |
| +-----------------------------------+ +------------------------------------+ |
|                                                                              |
| (the four panels follow: suitability, impact, risk, controls)                |
+------------------------------------------------------------------------------+
```

Partial, with the hourly cost unknown:

```text
| +-----------------------------------+ +------------------------------------+ |
| | Savings unknown                   | | Payback unknown                    | |
| |                                   | |                                    | |
| | Current cost      Unknown ////////| | 18000 |- - - - - - - - - - - - - - | |
| | Gross savings     Unknown ////////| |       |  investment                | |
| | Tooling              =>        150| |       |  ///// savings unknown /// | |
| | After automation  Unknown ////////| |     0 +--+--+--+--+--+--+--+--+--  | |
| |                                   | |       0  1  2  3  4  ...       12  | |
| | (i) Hourly cost not set. [ Set it in process settings ]                  | |
| +-----------------------------------+ +------------------------------------+ |
```

Mobile, 375 px:

```text
+-----------------------------------+
| Business case           [ Print ] |
| From your assumptions: implemen-  |
| tation 18000.00, tooling 150.00 a |
| month, a reduction on 5 of 7      |
| steps. [ Change on Analyse ]      |
|                                   |
| Saves 4420.00 a month             |
| Current cost     ########## 6800  |
| Gross savings       <====== 4570  |
| Tooling             =>       150  |
| After automation ####       2380  |
| [ Show as a table ]               |
|                                   |
| Pays back in month 4.1            |
| 53040 |                    ..o    |
|       |             ...''         |
| 18000 |- - x- - - - - - - - -     |
|       | .' investment             |
|     0 +--+--+--+--+--+--+--       |
|       0     3     6     9    12   |
| [ Show as a table ]               |
+-----------------------------------+
```

Decisions for both sizes:

- **The charts stack on mobile**, saving first: it is the answer the payback depends on.
- **The curve labels every third month on mobile**, and every month from 1280 px.
- **Screen readers get the table.** Each chart is drawn for the eye and hidden from assistive technology, and a table with the same figures sits next to it, visually hidden until "Show as a table" reveals it (`aria-expanded` on the button).
- **Touch targets of at least 44 by 44 px** for Print, the links and the table buttons.

### 7. Open questions

- Does "After automation" read clearly as the last bar, or do people expect the net saving there?
- Do people find the crossing month without reading the title?
- Does the printed page fit on one A4 sheet with a dozen steps in the panels below?

## Comparative heuristic evaluation

Do this once all the wireframes exist. Walk the three critical paths of `01-discovery.md` twice, once in the current client and once in your wireframes, at full width and at 375 px. To run the current client: `uv run uvicorn app.main:app --reload`, then open `http://localhost:8000/ui/`.

Severity scale (Nielsen): 0 not a problem, 1 cosmetic, 2 minor, 3 major (fix before release), 4 catastrophe (blocks the task).

| # | Heuristic | Ask yourself |
|---|---|---|
| 1 | Visibility of system status | While an LLM analysis runs (up to 200 s), do I know something is happening? |
| 2 | Match with the real world | Would an operations lead understand "occurrence rate", "rule clarity" or "RULE_BASED"? |
| 3 | User control and freedom | Can I undo a delete or leave a form without losing work? |
| 4 | Consistency and standards | Do tabs, buttons and badges behave the same everywhere? |
| 5 | Error prevention | What stops me from entering 50 as an occurrence rate between 0 and 1? |
| 6 | Recognition over recall | On Results, do I still remember the assumptions I typed on Analyse? |
| 7 | Flexibility and efficiency | How many clicks to edit five steps in a row? |
| 8 | Aesthetic and minimalist design | Which text on each page would nobody miss? |
| 9 | Recover from errors | Does a 422 tell me what to change and where? |
| 10 | Help and documentation | Where would a first-time visitor learn what suitability means? |

| # | Path and page | Heuristic | Problem (what happens, not the fix) | Old client | New wireframe |
|---|---|---|---|---|---|
| 1 | | | | severity | severity |

A problem with severity 3 or 4 in the new wireframe sends that screen back to step 4.
