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

Apply the seven steps to the Steps page of a process (RS-74), in Penpot, in greyscale, at 1280 and 375 px. It is the hardest screen of the client: a step has fifteen fields, and the page must show several steps at once.

Questions to help you with ranking and alternatives:

- Which three facts about a step does someone need to see in the list, and which only when editing?
- Edit in a dialog, in a side panel, inline in the list, or on its own page? Sketch at least three of these.
- How do you reorder steps with the keyboard and on a touch screen, without relying on drag and drop?
- What does the page look like with zero steps, with one, and with twelve?
- How do you show that "Exception rate" is unknown and not zero?

Write your result as a new section of this document, with the same seven headings as the worked example. I review it before you move on to the next screen.

Then, in order: Analyse (RS-75), Results (RS-75, RS-76), Blueprint and History (RS-76).

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
