# ADR 0021: Retrieval over the sector catalog with a swappable embedder

**Status:** proposed · 2026-11-08 · completes PDR 005

## Context

PDR 005 grounds the drafts of RU-14 in the sector catalog: before the model drafts the steps of a described process, the API retrieves the closest catalog processes. The catalog is small and owned by the project: seven JSON files, 21 processes, about a hundred steps, no numbers, loaded by `TemplateService`. The repo has no embeddings, vectors or search today, and `LLMProvider` (ADR 0004) has a single method, `analyze_process`. Anthropic offers no embedding model; its documentation points to Voyage AI.

## Decision

- **An `Embedder` protocol of its own.** A new package `src/app/retrieval/` holds `Embedder` with `name`, `model` and `embed(texts, input_type)`, where `input_type` is `query` or `document`. It stays apart from `LLMProvider`: embedding and generation change for different reasons and come from different vendors. Services depend on the protocol, never on an SDK, and `tests/unit/test_boundaries.py` forbids `voyageai` in `services/`.
- **Fake by default.** `FakeEmbedder` hashes the words of a text into a fixed-size normalised vector: deterministic, offline, and close enough to keyword overlap that tests can assert what it retrieves. Settings gain `embedding_provider` (`fake` or `voyage`, default `fake`), `voyage_api_key` and `voyage_model` (default `voyage-4-lite`). CI and the demo need no key, as with the LLM.
- **Voyage first.** `VoyageEmbedder` calls Voyage through the official `voyageai` client, the one new dependency, pinned and updated under ADR 0010. SDK errors map to the provider errors of `src/app/llm/`, so a failed embedding fails the draft the way a failed generation does.
- **One chunk per step, with its context.** Each step becomes one text that starts with its sector and process: "Insurance. Claims intake. Check the policy and the cover: ..." followed by its description, role and tools. Each process adds one chunk with its name, description and step names. A step alone ("Check the data") is ambiguous; with its process in front it is not.
- **Offline index, online query.** `scripts/build_catalog_index.py` embeds the catalog as `document` and writes `src/app/catalog/index/<model>.json` with the vectors and a hash of the catalog files. A test fails when the hash no longer matches, so a catalog change without a rebuilt index never merges. The fake index is built at startup instead, since it costs nothing. A request embeds only the description, as `query`.
- **Ranking is pure and lives in the domain.** `src/app/domain/retrieval.py` takes the query vector and the index and returns the ranked processes: cosine similarity per chunk (a dot product, since vectors are normalised), the score of a process is the best score of its chunks, the top 3 above a threshold are kept, each with its best steps. Similarity is a float; it never touches money or hours. Mutation testing covers it with the rest of the domain (ADR 0011).
- **A threshold, tuned on the gold set.** Below it, a process is not retrieved. With none above it, the draft goes ahead ungrounded and says so (PDR 005). The value is a setting per model, chosen from the evaluation below.
- **Grounding through the structured output.** The retrieved processes enter the draft prompt as reference blocks, and `PROMPT_VERSION` of the draft prompt records the change. Each drafted step carries `grounded_on`, the slug of a retrieved process or null. Python checks every slug against the retrieved set and rejects a draft that names any other, as it rejects a schema error. `grounded_on` is text; the output schema still has no numeric field (hard rule 2).
- **Retrieval is evaluated apart from generation.** A gold set in `tests/` pairs short descriptions, written like a visitor would, with the catalog process each should find. With `FakeEmbedder` a test asserts recall@3 and mean reciprocal rank above fixed floors in CI. With Voyage the same set runs by manual dispatch next to `tests/provider/`, and its result sets the threshold and the target of PDR 005. Following ADR 0012, this is the first part of the LLM eval dataset.

## Consequences

- RAG enters the product, limited to the catalog. The pieces are each small enough to read in one sitting: chunking, an embedder, an index file, a ranking function, a prompt section and a check.
- One vendor and one key more. `embedding_provider=voyage` without `voyage_api_key` fails at startup, like the Anthropic provider, instead of falling back silently.
- A catalog change costs one script run and one more file in the pull request.
- Retrieval quality is a number in CI, so a change to chunking or the threshold shows whether it helped.
- A step names its source, so the review screen of RS-99 can show "Based on: <process>".

## Alternatives rejected

| Alternative | Why not |
|---|---|
| pgvector or a vector database | About 120 vectors fit in memory and rank in microseconds. Revisit past some ten thousand chunks or with content per visitor |
| Native `search_result` blocks with citations | Claude cites them well, but the API rejects citations together with structured output, which ADR 0004 and hard rule 2 rely on. `grounded_on` keeps the schema and is checked by Python |
| An `embed` method on `LLMProvider` | Couples two vendors and two concerns; the Anthropic adapter would have nothing to implement |
| A local open-weight model (`voyage-4-nano` or similar) | No key, but a large runtime and model download in the API image for a corpus this small |
| Keyword search only (BM25) | No dependency, but misses a description that uses other words than the catalog. Kept in mind as the hybrid half if evaluation shows exact terms matter |
| Whole processes as the only chunks | Coarser: the draft needs to know which steps matched, not only which process |
| A reranker | Another call and vendor product with only 21 candidates to order |

## How to revert

Set `embedding_provider` back to `fake` and stop sending the retrieved block in the prompt: the draft of RS-98 works ungrounded, with `grounded_on` null on every step. Removing the package, the index files, the dependency and the setting is one pull request.
