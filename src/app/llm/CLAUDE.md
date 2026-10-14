# LLM layer

The contract with the model and its adapters. Services depend on the `LLMProvider` protocol in `provider.py`, never on an SDK.

## Read

- `docs/adr/0004-provider-agnostic-llm-anthropic-first.md`
- `docs/adr/0001-deterministic-first-analysis.md` (what the model may and may not decide)

## Rules

- Hard rule 2: `LLMAnalysisOutput` in `schemas.py` has no field for hours, cost, score, savings, payback or ROI, and rejects extra fields.
- Hard rule 3: the model may raise a human control and never lower it; the domain enforces it in reconciliation.
- A change to the prompt updates `PROMPT_VERSION` in `prompts.py`, which is stored with each analysis.
- Full prompts are never logged.
- SDK errors map to `LLMProviderError` subclasses (timeout, invalid output, refusal, configuration), so an outage degrades the analysis instead of failing it.
- `FakeLLMProvider` stays deterministic: it is the default for the demo and CI.
- A new provider is one module in `providers/` implementing `name`, `model` and `analyze_process`.

## Verify

```bash
uv run pytest tests/unit/llm
```

`tests/provider/` calls the real API and runs only by manual dispatch of `.github/workflows/llm-contract.yml`.
