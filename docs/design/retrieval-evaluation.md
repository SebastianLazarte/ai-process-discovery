# Retrieval evaluation (RS-119)

The offline check uses 42 synthetic English visitor descriptions and 10 descriptions
outside the catalog. Each of the 21 current processes has a direct request and a freer
paraphrase in `tests/fixtures/retrieval_gold.json`. These are authored examples, not real
visitor records or a human-reviewed benchmark. They were written before measuring scores
and left unchanged during calibration. A test compares their labels with the live catalog:
adding a process requires adding at least two examples, and removing one requires updating
its labels. Catalog growth is not hidden behind a fixed process count.

## Run it

```bash
uv run python scripts/evaluate_retrieval.py --check
uv run python scripts/evaluate_retrieval.py --sweep 0 0.30 0.32 0.34 0.35 0.36 0.40 0.60
uv run pytest tests/unit/test_retrieval_evaluation.py
```

The script always runs the fake embedder offline, regardless of `.env` or provider
environment variables. Its JSON includes the model, catalog hash, gold version and hash,
threshold, metrics and each case's ranking. It includes case ids rather than descriptions.
`--check` exits with status 1 when a floor fails. `--sweep` compares thresholds on the same
index and gold set; combined with `--check`, the gate applies to the calibrated default,
not to every exploratory threshold. The ordinary pytest suite runs the regression gates
in CI on both Python versions and PostgreSQL. It needs no new job or credentials.

## What the metrics mean

- **Recall@3:** positive descriptions whose expected process is among the first three
  results, divided by all positive descriptions. An empty result counts as a miss.
- **MRR:** mean reciprocal rank over those same positives, using 1, 1/2 or 1/3 for ranks
  one to three and zero for a miss. It is truncated at three because the product returns
  at most three processes.
- **No-match accuracy:** negative descriptions returning nothing, divided by all negative
  descriptions. Negatives never inflate recall or MRR.

## Calibration on 2026-11-12

The original `fake-hash-256` with the provisional threshold of 0.60 scored recall 0.2381,
MRR 0.2262 and no-match accuracy 0.90. In particular, the theatre rehearsal description
retrieved customer support with similarity 0.6502. Common English function words dominated
some short inputs. Raising the threshold alone discarded still more valid queries.

`fake-hash-256-v2` removes a fixed, general list of English function words before hashing.
It keeps the 256 dimensions, deterministic hashing and normalisation. It has no stemming,
synonym expansion or semantic understanding. Its new model id prevents mixing old vectors
or an old calibration with the changed tokenisation. The index remains in memory.

| v2 threshold | Recall@3 | MRR | No-match accuracy |
|---|---:|---:|---:|
| 0.00 | 0.8333 | 0.7659 | 0.00 |
| 0.30 | 0.7143 | 0.7024 | 0.80 |
| 0.32 | 0.6905 | 0.6786 | 0.90 |
| 0.34 | 0.6667 | 0.6548 | 0.90 |
| **0.35** | **0.6429** | **0.6310** | **1.00** |
| 0.36 | 0.6190 | 0.6071 | 1.00 |
| 0.40 | 0.5238 | 0.5238 | 1.00 |

The selected threshold, 0.35, is the lowest hundredth in the sweep that rejects every
negative. The highest negative score is 0.3462, so the margin is small. The fixed CI floors
are recall >= 0.60, MRR >= 0.60 and no-match accuracy = 1.00. They detect regressions in
this deterministic baseline; they are not a production quality target.

At 0.35, 27 of 42 positives are recovered: 26 at rank one and one at rank two. All 15 misses
are freer paraphrases. Fourteen return nothing, while the supplier-bills paraphrase returns
purchase orders instead of invoice processing. The report preserves these failures. Even
without a threshold, seven positives miss the top three. This fake does not meet PDR 005's
0.90 recall target for the production embedding model.

The same small set was used to calibrate the threshold and measure it. These scores do
not estimate performance on unseen visitors, other languages or every out-of-catalog
request. Before a production quality claim, add independently reviewed held-out examples,
including nearby unsupported processes, and evaluate the real model under RS-120. The
generic `evaluate(cases, retrieve)` function can score that service without changing the
gold set or metric definitions. No Voyage call or production threshold was measured here.

## Settings and migration

`RETRIEVAL_THRESHOLDS` is a JSON map keyed by the exact embedding model id:

```dotenv
RETRIEVAL_THRESHOLDS={"fake-hash-256-v2":0.35}
```

An unknown model without a calibrated entry fails startup with a configuration error.
Values must be finite and within [-1, 1]. An explicitly set legacy `RETRIEVAL_THRESHOLD`
still overrides the map, including zero. Remove an old `RETRIEVAL_THRESHOLD=0.6` from local
or deployment configuration to use the new calibrated default. No deployment settings
are changed by this PR. Add a real-model entry only after its own evaluation; a fake
threshold is not transferred to Voyage.
