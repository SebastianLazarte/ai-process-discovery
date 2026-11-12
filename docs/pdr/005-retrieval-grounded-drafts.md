# PDR 005: Drafts grounded in the sector catalog

**Status:** proposed · 2026-11-08 · amends PDR 001 (the non-goal "No RAG", for the catalog only)

## Problem

Epic RU-14 lets a visitor describe a process in their own words and get a draft of its steps (RS-98 to RS-101, block B14). A model that drafts from a free description alone invents steps, roles and tools that only sound right, and the visitor cannot tell which ones came from where. The sector catalog of RU-13 already holds 21 reviewed processes in seven sectors, step by step, with no numbers in them. A draft built from scratch ignores all of that.

## Decision

The draft of RU-14 is grounded in the catalog through retrieval: retrieval-augmented generation (RAG) over content the project owns.

- **Retrieve, then draft.** Before the model drafts, the API finds the catalog processes and steps closest to the description and passes them to the model as reference. The model adapts them to the description; it does not copy them blindly and it does not draft without them when a close match exists.
- **Every step says where it came from.** Each drafted step names the catalog process it was based on, or says that no catalog process was close enough. The review screen of RS-99 shows "Based on: <process>" next to the AI badge, so the visitor sees which parts are borrowed and which are new.
- **No close match is an answer.** When nothing in the catalog is close enough, the draft says so and is marked as ungrounded. The API never stretches an unrelated process to fit.
- **Only the catalog.** Retrieval reads the JSON files of `src/app/catalog/`, which the maintainer reviews in pull requests. Nothing a visitor types or uploads is ever indexed or retrieved for anyone else.
- **Nothing changes for numbers.** The retrieved text feeds wording and structure only. Python still computes every hour, cost, score and saving (ADR 0001); the catalog has no numbers to leak (RS-95).
- **Same gates as RU-14.** Drafts stay off on the public demo until the input guardrails (RS-100, ADR 0017) and the daily quota (RS-101) merge.

ADR 0021 records how retrieval is built.

## Success criteria

- **Retrieval is measured on its own.** A gold set of descriptions, each with the catalog process it should find, reaches recall@3 of at least 0.9 with the production embedding model, checked in a manual run, and a fixed threshold with the fake model in CI.
- In the usability session of the design brief, a visitor who reads a grounded draft says which steps came from the catalog without help.
- Every drafted step names a retrieved catalog process or is marked as ungrounded. A step that names a process that was not retrieved fails the request.

## Non-goals

- Documents uploaded or pasted by visitors as a knowledge base.
- Chat or question answering over documents.
- A vector database, a reranker or hybrid keyword and vector search; ADR 0021 says when to revisit them.
- Retrieval for the analysis of a process (`analyze_process`): it interprets steps the visitor already confirmed.

## Consequences

- PDR 001's non-goal "No RAG" notes the amendment, as its "no hosted deployment" notes ADR 0008.
- One new external service, the embedding provider, with its own key; the fake embedder keeps the demo and CI free of keys, as the fake LLM provider does (ADR 0004).
- The backlog of RU-14 gains retrieval, its evaluation and the grounding of the draft. They are RS-116 to RS-122, approved by the Product Owner on 2026-11-12.
- Adding or changing a catalog process changes what drafts can be grounded in, so the catalog index is rebuilt with it.
