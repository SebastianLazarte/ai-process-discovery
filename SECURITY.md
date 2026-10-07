# Security

Report vulnerabilities through GitHub's private vulnerability reporting (Security tab → Report a vulnerability). Do not open a public issue.

What the project does by design:

- API keys only through environment variables; secret scanning with push protection is enabled.
- Steps flagged as handling sensitive data are not sent to the LLM provider without explicit confirmation.
- Prompts and step descriptions are never written to logs.
- Monetary inputs are never sent to the LLM provider.
- The demo has no authentication. Do not expose it on a public network with real data.
